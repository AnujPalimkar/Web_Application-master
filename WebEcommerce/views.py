from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView, View
import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from ManorPharmacy.forms import CheckoutForm
from ManorPharmacy.util import *
from adminpanel.models import *
import stripe

from datetime import datetime
from datetime import timedelta
from dateutil import parser
import dateutil.parser

import icalendar
from icalendar import Calendar, Event
from icalendar import vCalAddress, vText
import tempfile, os
from django.core.mail import send_mail, EmailMultiAlternatives


stripe.api_key = settings.STRIPE_SECRET_KEY


def index(request):
    context = {}
    return render(request, 'webecommerce/index.html', context)


# This function is the main home page of the client login and display the Announcements (or promotions)/
# All products and services.

class IndexView(ListView):
    model = Product
    template_name = 'webecommerce/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        products = Product.objects.filter(IsProduct=1)
        services = Product.objects.filter(IsProduct=0)
        context['products'] = products
        context['services'] = services
        # FETCH image of dashboard/index page
        context['DashboardImage'] = Configuration.objects.filter(ConfigurationName__icontains='DASHBOARD')
        # Fetch values for Announcement/promotoion/Post.
        context['AnnouncementPost'] = AnnouncementPost.objects.filter(IsActive=1)
        # Fetch Cart Details for customers to display on cart hover.
        orderitems = {}
        if self.request.user.id is not None:
            customer = self.request.user.customer
            try:
                order = Order.objects.get(Customer=customer, IsOrderCompleted=False)
                orderitems = order.orderdetails_set.all()
            except ObjectDoesNotExist:
                order = {}
        context['orderitems'] = orderitems

        return context


# This function lands the user on the shopping page which displays Products and services.
def shop(request):
    context = {}
    return render(request, 'webecommerce/shop.html', context)


class ShopView(ListView):
    model = Product
    template_name = 'webecommerce/shop.html'

    def get_context_data(self, **kwargs):
        context = super(ShopView, self).get_context_data(**kwargs)
        allProducts = []
        products = Product.objects.filter(IsProduct=1)
        allProducts.append(products)
        services = Product.objects.filter(IsProduct=0)
        allProducts.append(services)
        context['allProducts'] = allProducts
        # Fetch Cart Details for customers to display on cart hover.
        customer = self.request.user.customer
        try:
            order = Order.objects.get(Customer=customer, IsOrderCompleted=False)
            orderitems = order.orderdetails_set.all()
        except ObjectDoesNotExist:
            order = {}
            orderitems = {}

        context['orderitems'] = orderitems
        # And so on for more models
        return context


def shopByCategory(request):
    # cart items is for displaying the total no of items in the cart (icon).

    allProducts = []
    category = request.POST.get("category")
    if category == "1":
        products = Product.objects.filter(IsProduct=1)
        allProducts.append(products)
    elif category == "2":
        products = Product.objects.filter(IsProduct=0)
        allProducts.append(products)
    else:
        products = Product.objects.filter(IsProduct=1)
        allProducts.append(products)
        services = Product.objects.filter(IsProduct=0)
        allProducts.append(services)
    context = {'allProducts': allProducts}
    html = render_to_string('webecommerce/searchbycategory.html', context)
    return JsonResponse(html, safe=False)


# This function represents the detail view of any selected product / service.
# From here, user can add the product into the cart.
class DetailView(DetailView):
    model = Product
    template_name = 'webecommerce/detail.html'


# This function represents the total items which are added in the shopping cart.
# It also show the discount amount: If user wants to pay full amount in one go,
# then he is eligible for 10% flat discount.
def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    items = data['items']
    order = data['order']
    # Get the % amount for Full payment discount. This will be managed by Admin/Super admin.
    discountAmountForFullPayment = getFullPaymentDiscount(order, 'Fulltime Payment')
    # Full payment discount calculation.
    # Here, the Full Payment discount will be applied ONLY ON SERVICES.
    # Customer must pay full amount of purchased product at the tome of purchasing.
    totalAmountWithDiscount = order.get_TotalForAllProductPriceAndInitialSetupCharge_WithFullPayment - discountAmountForFullPayment

    context = {'items': items, 'order': order, 'cartItems': cartItems, 'itemCount': len(items),
               'discountAmountForFullPayment': discountAmountForFullPayment,
               'totalAmountWithDiscount': totalAmountWithDiscount}
    return render(request, 'webecommerce/cart.html', context)


# This function represents the total items which are added in the shopping cart along with the
# Shipping/Billing address and coupon code details. If customer has discount coupon code then he can apply the code
# and get another discount on total payment.

def checkout(request):
    STRIPE_PUBLISHABLE_KEY = settings.STRIPE_PUBLISHABLE_KEY

    form = CheckoutForm()
    isPayByInstallment = request.GET.get('data')
    data = cartData(request)
    cartItems = data['cartItems']
    items = data['items']
    order = data['order']
    customerdetail = data['customerdetail']
    currentDate = datetime.datetime.now()
    yearLimit = currentDate.year + 21
    yearList = []
    totalwithDiscount = 0

    # discountAmount = getDiscount(order, 'Fulltime Payment')
    discountAmountForFullPayment = getFullPaymentDiscount(order, 'Fulltime Payment')

    totalAmountWithDiscount = order.get_TotalForAllProductPriceAndInitialSetupCharge_WithFullPayment - discountAmountForFullPayment
    sameHouseHoldCustomerId = customerdetail[11]
    referralCustomerId = customerdetail[12]

    otherReferralDiscount = 0
    sameHouseHoldReferralDiscount = 0
    IsServiceExists = False
    IsProductExists = False
    discountOnProduct = 0
    discountPercentageOnProduct = 0

    for item in items:
        if item.Product.IsDiscountable and item.Product.IsProduct:
            discountPercentageOnProduct += item.Product.DiscountPercentage
        if item.Product.IsProduct:
            IsProductExists = True
        if not item.Product.IsProduct:
            IsServiceExists = True

        # TO DO: Get the discount of Product and calculate it.
        if order.get_CartTotalPriceForAllDiscountableProduct_WithFullPayment > 0:
            discountOnProduct = \
                (order.get_CartTotalPriceForAllDiscountableProduct_WithFullPayment * discountPercentageOnProduct) / 100

        fullDiscountAmount = 0
        if isPayByInstallment == 'no':
            fullDiscountAmount = getFullPaymentDiscount(order, 'Fulltime Payment')
            totalwithDiscount = order.get_TotalForAllProductPriceAndInitialSetupCharge_WithFullPayment - fullDiscountAmount - discountOnProduct
        else:
            totalwithDiscount = order.get_TotalPrice_WithInstallmentPayment - discountOnProduct

    # Customer Personal Discount
    customerPersonalDiscount = customerdetail[14]
    customerPersonalDiscountAmount = 0

    # if customerPersonalDiscount > 0:
    #     customerPersonalDiscountAmount = (totalwithDiscount * customerPersonalDiscount) / 100
    #     print('personal disc', customerPersonalDiscountAmount)
    #     totalwithDiscount = totalwithDiscount - customerPersonalDiscountAmount

    for i in range(currentDate.year, yearLimit):
        yearList.append(i)

    context = {'items': items, 'order': order, 'cartItems': cartItems, 'customerdetail': customerdetail,
               'yearLimit': yearList, 'totalwithDiscount': totalwithDiscount, 'isPayByInstallment': isPayByInstallment,
               'discountOnProduct': discountOnProduct,
               'discountAmountForFullPayment': fullDiscountAmount,
               'customerPersonalDiscountAmount': customerPersonalDiscountAmount,
               'IsServiceExists': IsServiceExists,
               'IsProductExists': IsProductExists,
               'form': form,
               'STRIPE_PUBLISHABLE_KEY': STRIPE_PUBLISHABLE_KEY
               }

    return render(request, 'webecommerce/checkout.html', context)


# This function updates all the necessary tables after placing an order and successful payment.
# The tables which needs to be updated are:
# Order, Payment, InstalmentDue, Product, OrderDiscount, CustomerDiscount
# Also, it will send the Invoice  as an attachment along with an email.
def placeOrder(request):
    transId = datetime.datetime.now().timestamp()

    data = json.loads(request.body)
    cookiedata = cartData(request)
    items = cookiedata['items']
    orderFromCookie = cookiedata['order']
    address = data['Shipping']
    paymentInInstalment = data['paymentInInstalment']
    serviceDiscount = data['serviceDiscount']
    serviceDiscountPercentage = data['serviceDiscountPercentage']
    serviceDiscountId = data['serviceDiscountId']

    try:
        customer = request.user.customer
        # Get / Create Order and payment based on the customer who has logged in.
        if request.user.is_authenticated:
            order, created = Order.objects.get_or_create(Customer=customer, IsOrderCompleted=False)
            payment, created = Payment.objects.get_or_create(Order=order)
        else:
            customer, order, payment = guestOrder(request, data)

        total = float(data['User']['total'])
        payment.Amount = total
        payment.Payment_Type = data['paymentType']
        order.Transaction_Id = transId
        order.ActualAmountToPay = orderFromCookie.get_CartTotalPriceForInitialSetupAndProduct
        payment.save()
        order.save()

        serviceInstalmentMonth = 0
        # Update Instalment Due table if the payment is done by instalment.
        # Also, the instalment amount will be decided based on the number of customers selection.
        # If the service is for 2 family member then the price will be differ.
        if paymentInInstalment == 'yes':
            for item in items:
                if not item.Product.IsProduct:
                    if item.TotalNoOfPerson == 1:
                        serviceInstalmentMonth = item.Product.NoOfInstallmentMonths
                        price = item.Product.Price * item.Quantity
                        days = 28
                        # TODO: Create SP to insert values in database
                        if int(float(serviceDiscount)) > 0:
                            discountAmount = price * int(float(serviceDiscountPercentage)) / 100
                            price = price - discountAmount
                        for i in range(1, serviceInstalmentMonth + 1):
                            # Logic for the instalment cycles:
                            # Customer has to pay his Fist instalment after 14 days of from the purchase date.
                            # For e.g. if customer purchased any service on 1st December then ,
                            # the next instalment will be after 14 days, i.e. 15th December.
                            # Then the second instalment will be after 28 days from the actual purchase date.
                            # (as per above e.g., it will be on 30th December).
                            # And now next all instalments will be after 28 days from the LAST instalment.
                            if i == 1:
                                days = 14
                            else:
                                days += 28
                            todaysdate = datetime.timedelta(days=days)
                            duedate = datetime.date.today() + todaysdate
                            installment_due = InstallmentDue.objects.create(Order=order)
                            installment_due.Due_Installments = i
                            installment_due.Amount_Due = price
                            installment_due.InstalmentDueDate = duedate
                            installment_due.Customer_Id = customer.Customer_Id
                            installment_due.User_Id = request.user.id
                            installment_due.IsInstalmentPaid = 0
                            installment_due.OrderDetail_id = item.id
                            installment_due.save()  #
                            if i == 1:
                                days = 0
                    else:
                        serviceInstalmentMonth = item.Product.NoOfInstallmentMonths
                        price = (item.Product.Price + item.Product.AdditionalMemberPrice) * item.Quantity
                        if int(float(serviceDiscount)) > 0:
                            discountAmount = price * int(float(serviceDiscountPercentage)) / 100
                            price = price - discountAmount
                        for i in range(1, serviceInstalmentMonth + 1):
                            if i == 1:
                                days = 14
                            else:
                                days += 28

                            todaysdate = datetime.timedelta(days=days)
                            duedate = datetime.date.today() + todaysdate
                            installment_due, created = InstallmentDue.objects.get_or_create(Order=order)
                            installment_due.Due_Installments = i
                            installment_due.Amount_Due = price
                            installment_due.InstalmentDueDate = duedate
                            installment_due.Customer_Id = customer.Customer_Id
                            installment_due.User_Id = request.user.id
                            installment_due.IsInstalmentPaid = 0
                            installment_due.OrderDetail_id = item.id
                            installment_due.save()  #
                            if i == 1:
                                days = 0
                    if int(float(serviceDiscount)) > 0:
                        order.ServiceDiscountAmount = serviceDiscount
                        order.ServiceDiscountCode = serviceDiscountId
        else:
            fullDiscountAmount = getFullPaymentDiscount(order, 'Fulltime Payment')
            order.FullPaymentDiscountAmount = fullDiscountAmount

        try:
            # Payment Integration
            token = data['token']  # request.POST.get("stripeToken")
            paymentDescription = 'Payment Done by ' + data['User']['name']
            charge = stripe.Charge.create(
                amount=int(total * 100),
                currency="gbp",
                source=token,
                description=paymentDescription
            )
            message = ""

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            print('Status is: %s' % e.http_status)
            print('Code is: %s' % e.code)
            print('Param is: %s' % e.param)
            print('Message is: %s' % e.user_message)
            body = e.json_body
            err = body.get('error', {})
            messages.error(request, err.get('message'))
            print('error in placeOrder/CardError', err.get('message'))
            message = err.get('message')
            return JsonResponse({'status': 'false', 'message': message}, safe=False)
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(request, "RateLimitError")
            print('Error in placeOrder/ RateLimitError:', str(e))
            message = str(e)
            return JsonResponse({'status': 'false', 'message': message}, safe=False)
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(request, "InvalidRequestError")
            print('Error in placeOrder/InvalidRequestError:', str(e))
            message = str(e)
            return JsonResponse({"status": 'false', "message": message}, safe=False)
            print('after json')
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(request, "AuthenticationError")
            print('Error in placeOrder/AuthenticationError:', str(e))
            message = str(e)
            return JsonResponse({'status': 'false', 'message': message}, safe=False)
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(request, "APIConnectionError")
            print('Error in placeOrder/APIConnectionError:', str(e))
            message = str(e)
            return JsonResponse({'status': 'false', 'message': message}, safe=False)
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error("StripeError")
            print('Error in placeOrder/StripeError:', str(e))
            message = str(e)
            return JsonResponse({'status': 'false', 'message': message}, safe=False)
        except Exception as e:
            print('Error in placeOrder function:', str(e))
            # messages.error(request, "There is some issue while processing order")

        print('Change the quantity')
        # Deduct the quantity of the product after purchasing. It will be managed by Admin/Super admin
        # Also, admin can see whether there is sufficient amount of products in stock or not.
        for item in items:
            if item.Product.IsProduct:
                qty = item.Product.StockLevel - item.Quantity
                product = Product.objects.get(Product_Id=item.Product.Product_Id)
                product.StockLevel = qty
                product.save()

        # Update details in OrderDiscount Table
        # To keep the record of discount for every order.

        if int(float(serviceDiscount)) > 0:
            order_discount, created = OrderDiscount.objects.get_or_create(Order=order)
            order_discount.DiscountType_Id = serviceDiscountId
            order_discount.save()

            customerDiscountApplicableLimit = serviceInstalmentMonth
            # Based on the count update the customerDiscountApplicableLimit value.
            # store details in CustomerDiscount Table
            # So, once a customer has applied the discount code, it will not be applicable for next purchase.

            customer_discount, created = \
                CustomerDiscountEligibility.objects.get_or_create(Customer=customer,
                                                                  Customer_id=customer.Customer_Id,
                                                                  DiscountType_Id=serviceDiscountId)
            customer_discount.DiscountType_Id = serviceDiscountId
            customer_discount.DiscountApplicableLimit = customerDiscountApplicableLimit
            customer_discount.IsUsed = 1
            customer_discount.save()
            print('Customer discount saved')

        order.IsOrderCompleted = True
        # Set current date for order completion date
        order.OrderStatus_id = 1
        order.save()

        subject = 'Invoice for your order.'
        fromEmail = settings.EMAIL_HOST_USER
        to_list = [data['User']['email']]
        try:
            html_content = render_to_string("emailInvoice/InvoiceContent.html", {'username': data['User']['name']})
            text_content = strip_tags(html_content)
            emailsend = EmailMultiAlternatives(
                subject,
                text_content,
                fromEmail,
                to_list
            )
            data = {
                'items': items,
                'order': order,
                'username': data['User']['name'],
                'address': address,
                'email': data['User']['email']
            }
            emailsend.attach_alternative(html_content, "text/html")
            pdf = render_to_pdf('pdf/invoice.html', data)
            emailsend.attach('invoice.pdf', pdf, 'file/pdf')
            emailsend.send()
            print('email sent')
        except Exception as e:
            print('in catch for email send')
            print('Error Is:', str(e))
            messages.error(request, "There is some issue while generating pdf")
        payment.Is_Invoice_Sent = True
        payment.Stripe_Payment_Id = charge.stripe_id
        payment.save()
        print('Invoice sent')
    except Exception as e:
        print('Error Is:', str(e))
        # messages.error(request, "There is some issue while processing order")
    finally:
        connection.close()
    print('completed')
    message = 'Payment Completed...!'
    return JsonResponse({'status': 'true', 'message': message}, safe=False)


# After the customer has successfully paid the amount, it will redirect the customer on the Thank you page.
# TODO: modify the html content.
class ThankYouView(ListView):
    model = Product
    template_name = 'webecommerce/thankyou.html'


def makeAppointment(request):
    cursor = connection.cursor()
    cursor.execute("call GetPractitionerList()")
    results = cursor.fetchall()
    userId=request.user.id
    cursor.callproc('getCustomer',[userId])
    results1 = cursor.fetchall()
    context = {"practitioner_list": results}
    if request.method=='POST':
        practitioner=request.POST.get("id1",None)
        context.update({"practitioner": practitioner})
        cursor.callproc('clientviewAvailableSlots',[practitioner])
        resultslot = cursor.fetchall()
        resultslot1=list(resultslot)
        res = [list(ele) for ele in resultslot1]
        for iterator in range(len(res)):
            res[iterator][4]=res[iterator][4].isoformat()
            res[iterator][5]=res[iterator][5].isoformat()
        context.update({'viewAvailableSlots1': res})
        cursor.callproc('clientviewDates',[practitioner])
        results3 = cursor.fetchall()
        context.update({'viewDates': results3})
        cursor.callproc('clientViewCalendarAppointment',[results1,practitioner])
        results4=cursor.fetchall()
        print(results4)
        resultslot4=list(results4)
        res4 = [list(ele) for ele in resultslot4]
        for iterator in range(len(res4)):
            res4[iterator][6]=res4[iterator][6].isoformat()
            res4[iterator][7]=res4[iterator][7].isoformat()
        context.update({'viewBookedSlots': res4})
        return JsonResponse(context)
    return render(request,'AppointmentBooking/appointmentForm.html',context)

def BookAppointment(request):
    cursor = connection.cursor()
    if request.method=='POST':
        practitionerid=request.POST.get('practitionerid')
        UserId=request.user.id
        cursor.callproc('getCustomer',[UserId])
        customerid = cursor.fetchall()
        cursor.callproc('GetCustomerDetailsById',[customerid])
        clientdetails=cursor.fetchall()
        clientemail=clientdetails[0][3]
        clientname=clientdetails[0][1]+''+clientdetails[0][2]
        start=request.POST.get('start')
        end=request.POST.get('end')
        startTime=dateutil.parser.isoparse(start)
        endTime=dateutil.parser.isoparse(end)
        thirty_min_timestamps = []
        date_x = startTime
        while date_x < endTime:
            thirty_min_timestamps.append(datetime.time(date_x))
            date_x += timedelta(minutes=30)
        slotid=[]
        for timestart in thirty_min_timestamps:
            cursor.callproc('getSlotId',[timestart])
            slotid.append(cursor.fetchall())
        cursor.callproc('bookappointment',[customerid,practitionerid,datetime.date(startTime),datetime.time(startTime),datetime.time(endTime)])
        appointmentid=cursor.fetchall()
        request.session['apptid']=appointmentid
        for idkey in slotid:
            cursor.callproc('updateCalendarSlot',[datetime.date(startTime),idkey[0][0],practitionerid,appointmentid])
        cal = Calendar()
        cal.add('prodid', '-//My calendar product//mxm.dk//')
        cal.add('version', '2.0')
        eventstart=datetime.fromisoformat(start.replace('Z', ''))
        eventend=datetime.fromisoformat(end.replace('Z', ''))
        event = Event()
        event.add('summary', 'Appointment Confirmed')
        event.add('dtstart',eventstart)
        event.add('dtend',eventend)
        organizer = vCalAddress('MAILTO:%s' % settings.EMAIL_HOST_USER)
        organizer.params['cn'] = vText('Prolongevity')
        organizer.params['role'] = vText('Practitioner')
        event['organizer'] = organizer
        event['location'] = vText('St Albans')
        attendee = vCalAddress('MAILTO:%s' % clientemail)
        attendee.params['cn'] = vText('%s' % clientname)
        attendee.params['ROLE'] = vText('PARTICIPANT')
        event.add('attendee', attendee, encode=0)
        cal.add_component(event)
        subject = 'Your Appointment Confirmation'
        fromEmail = settings.EMAIL_HOST_USER
        to_list = [clientemail]
        try:
            text_content = 'Thank you for booking an appointment.'

            emailsend = EmailMultiAlternatives(
                subject,
                text_content,
                fromEmail,
                to_list
            )
            emailsend.attach_alternative(text_content, "text/html")
            emailsend.attach('calcheck.ics', cal.to_ical())
            emailsend.send()
        except Exception as e:
            print('Error in sending email while registration'+str(e))
        return redirect(ViewAppointment)

def ViewAppointment(request):
    cursor = connection.cursor()
    UserId=request.user.id
    cursor.callproc('getCustomer',[UserId])
    customerid = cursor.fetchall()
    cursor.callproc('viewAppointment',[customerid])
    result=cursor.fetchall()
    context={"Appointment_Details":result}
    return render(request,'AppointmentBooking/AppointmentList.html',context)

def DeleteAppointment(request,id):
    cursor=connection.cursor()
    if request.method=='POST':
        cursor.callproc('DeleteAppointment',[id])
        return redirect('/ViewAppointment')

def DeleteAppointment1(request):
    cursor=connection.cursor()
    if request.method=='POST':
        id=request.POST.get('id',None)
        cursor.callproc('DeleteAppointment',[id])
        data = {}
        return JsonResponse({'success':True})