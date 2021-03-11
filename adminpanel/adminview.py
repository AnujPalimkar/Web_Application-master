from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import ListView
from django.http import JsonResponse

import random
import string

from ManorPharmacy.util import *

from adminpanel.adminform import *
from adminpanel.models import *
from django.db import connection
from django.db.utils import OperationalError

from django.contrib.auth.decorators import login_required
from adminpanel.CustomUserDecorator import CustomDecorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string, get_template
from django.utils.html import strip_tags
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseRedirect

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

from datetime import datetime
from datetime import timedelta
from dateutil import parser
import dateutil.parser

import icalendar
from icalendar import Calendar, Event
from icalendar import vCalAddress, vText
import tempfile, os

from django import template
register = template.Library()


@login_required(login_url='Login')
def home(request):
    group_name = None
    print('in  adminview home')
    if request.user.groups.values_list('name', flat=True).exists():
        group_name = request.user.groups.all()[0].name
    if group_name.lower() == 'client':
        return redirect('index')
    elif group_name.lower() == 'practitioner':
        userId=request.user.id
        cursor1 = connection.cursor()
        cursor1.callproc('viewBookedSlots',[userId])
        context={}
        resultslotbooked = cursor1.fetchall()
        if resultslotbooked:
            context.update({'eventbooked':resultslotbooked})
        return render(request, "practitionerpanel/homecontent.html",context)
    else:
        return render(request, "adminpanel/home_content.html")


@login_required(login_url='Login')
# @CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
@CustomDecorator.admin_only
def dashboard(request):
    # context = {"customer_list": Customer.objects.all()}
    print('IN DASHBOARD')
    return render(request, "admin/index.html")


@login_required(login_url='Login')
def DashboardHome(request):

    cursor = connection.cursor()
    cursor.execute("call GetProductStockDetails()")
    products = cursor.fetchall()
    print('Product Qty WIse', products)

    cursor.execute("call GetLatestOrders()")
    latestOrder = cursor.fetchall()

    context = {"products": products, 'latestOrder': latestOrder}
    return render(request, "adminpanel/dashboardhome.html", context)


@login_required(login_url='Login')
def customer_list(request):
    # context = {"customer_list": Customer.objects.all()}

    cursor = connection.cursor()
    cursor.execute("call GetCustomerList()")
    results = cursor.fetchall()
    context = {"customer_list": results}
    return render(request, "adminpanel/customer/customerlist.html", context)


@login_required(login_url='Login')
def customer_operation_sp(request, id=0):
    if request.method == "GET":
        if id == 0:
            customer = CustomerForm()
        else:
            try:
                cursor = connection.cursor()
                cursor.callproc('GetCustomerDetailsById', [id])
                customer = cursor.fetchone()
                print(customer)
                # Customer output = ('John', 'Peter', 'john@gmail.com', '1234567898', 'Male')
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/customer/customeroperation.html", {'form': customer})
    else:
        if id == 0:
            print('ID = 0')
            form = CustomerForm(request.POST)
        else:
            print('POST REQ')
            customer = Customer.objects.get(pk=id)
            form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
        else:
            print('There is an error')
        return redirect('/Customer')


@login_required(login_url='Login')
def customer_operation(request, id=0):
    if request.method == "GET":
        if id == 0:
            form = CustomerForm()
        else:
            customer = Customer.objects.get(pk=id)
            form = CustomerForm(instance=customer)
        return render(request, "adminpanel/customer/customeroperation.html", {'form': form})
    else:
        if id == 0:
            form = CustomerForm(request.POST)
        else:
            customer = Customer.objects.get(pk=id)
            form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
        return redirect('/Customer')


@login_required(login_url='Login')
def customer_delete(request, id):
    customer = Customer.objects.get(pk=id)
    customer.delete()
    return redirect('/Customer')


@login_required(login_url='Login')
def customerOrder(request, id=0):
    cursor = connection.cursor()
    print('customer order')
    print('Orders', id)
    cursor.callproc('GetPlanListByCustomerId', [id])
    results = cursor.fetchall()
    print(results)
    context = {"plans": results}
    return render(request, "adminpanel/customer/customerorders.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def discount_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetDiscountTypeList()")
    results = cursor.fetchall()
    context = {"discount_list": results}
    return render(request, "adminpanel/discount/discountlist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def discount_operation(request, id=0):
    if request.method == "GET":
        if id == 0:
            discount = DiscountTypeForm()
        else:
            # disc = DiscountType.objects.get(pk=id)
            # form = DiscountTypeForm(instance=disc)
            try:
                cursor = connection.cursor()
                cursor.callproc('GetDiscountTypeById', [id])
                discount = cursor.fetchone()
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/discount/discountoperation.html", {'form': discount})
    else:
        if id == 0:
            form = DiscountTypeForm(request.POST)
        else:
            disc = DiscountType.objects.get(pk=id)
            form = DiscountTypeForm(request.POST, instance=disc)
        try:
            if form.is_valid():
                form.save()
            else:
                print(form.errors)
        except OperationalError as e:
            print(format(e))
        return redirect('/Discount')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def discount_delete(request, id):
    disc = DiscountType.objects.get(pk=id)
    disc.delete()
    return redirect('/Discount')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def product_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetProductDetails()")
    results = cursor.fetchall()
    page = request.GET.get('page', 1)
    paginator = Paginator(results, 5)
    print('results', results)
    print(page)
    print(paginator)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    print('product result', products)
    context = {"product_list": products}
    return render(request, "adminpanel/product/productlist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def product_operation(request, id=0):
    categories = Category.objects.all()
    if request.method == "GET":
        if id == 0:
            product = ProductTypeForm()
        else:
            try:
                cursor = connection.cursor()
                cursor.callproc('GetProductById', [id])
                product = cursor.fetchone()
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/product/productoperation.html", {'form': product, 'categories': categories})
    else:
        if id == 0:
            form = ProductTypeForm(request.POST, request.FILES)
        else:
            prod = Product.objects.get(pk=id)
            IsProduct = request.POST.get("IsProduct")
            form = ProductTypeForm(request.POST, request.FILES, instance=prod)
        if form.is_valid():
            prod = form.save()
            prod.IsProduct = 1
            prod.save()
        else:
            print('Issue with Saving Product.')
        return redirect('/Product')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin'])
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def product_delete(request, id):
    prod = Product.objects.get(pk=id)
    prod.delete()
    return redirect('/Product')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def service_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetServiceDetails()")
    results = cursor.fetchall()
    context = {"service_list": results}
    return render(request, "adminpanel/service/servicelist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def service_operation(request, id=0):
    categories = Category.objects.all()
    if request.method == "GET":
        if id == 0:
            service = ServiceTypeForm()
        else:
            try:
                cursor = connection.cursor()
                cursor.callproc('GetProductById', [id])
                service = cursor.fetchone()
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/service/serviceoperation.html", {'form': service, 'categories': categories})
    else:
        if id == 0:
            print('id = 0')
            form = ServiceTypeForm(request.POST, request.FILES)
            print('form is', form)
        else:
            service = Product.objects.get(pk=id)
            form = ServiceTypeForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            print('form is valid')
            Service = form.save()
            Service.IsProduct = 0
            Service.save()
        else:
            print('Issue with Saving Service.')
        return redirect('/Service')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin'])
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def service_delete(request, id):
    service = Product.objects.get(pk=id)
    service.delete()
    return redirect('/Service')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def installment_list(request):
    # context = {"installment_list": InstallmentType.objects.all().order_by('-Installment_Type')}
    cursor = connection.cursor()
    cursor.execute("call GetInstallmentType()")
    results = cursor.fetchall()
    context = {"installment_list": results}
    return render(request, "adminpanel/installment/installmentlist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def installment_operation(request, id=0):
    if request.method == "GET":
        if id == 0:
            installmenttype = InstallmentTypeForm()
        else:
            # installment_type = InstallmentType.objects.get(pk=id)
            # form = InstallmentTypeForm(instance=installment_type)
            try:
                cursor = connection.cursor()
                cursor.callproc('GetInstallmentTypeById', [id])
                installmenttype = cursor.fetchone()
                print(installmenttype)
                # Customer output = ('John', 'Peter', 'john@gmail.com', '1234567898', 'Male')
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/installment/installmentoperation.html", {'form': installmenttype})
    else:
        if id == 0:
            form = InstallmentTypeForm(request.POST)
        else:
            installment_type = InstallmentType.objects.get(pk=id)
            form = InstallmentTypeForm(request.POST, instance=installment_type)
        if form.is_valid():
            form.save()
        return redirect('/Installment')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def installment_delete(request, id):
    disc = InstallmentType.objects.get(pk=id)
    disc.delete()
    return redirect('/Installment')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def usertype_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetUserType()")
    results = cursor.fetchall()
    context = {"usertype_list": results}
    return render(request, "adminpanel/Usertype/usertypelist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def usertype_operation(request, id=0):
    if request.method == "GET":
        if id == 0:
            usertype = UserTypeForm()
        else:
            try:
                cursor = connection.cursor()
                cursor.callproc('GetUserTypeById', [id])
                usertype = cursor.fetchone()
                print(usertype)
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/Usertype/usertypeoperation.html", {'form': usertype})
    else:
        if id == 0:
            form = UserTypeForm(request.POST)
        else:
            usertype = UserType.objects.get(pk=id)
            form = UserTypeForm(request.POST, instance=usertype)
        if form.is_valid():
            form.save()
        return redirect('/Usertype')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def usertype_delete(request, id):
    usertype = UserType.objects.get(pk=id)
    usertype.delete()
    return redirect('/Usertype')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def invoice_generation(request):
    context = {"product_list": Product.objects.all()}
    return render(request, "adminpanel/invoicetemplate.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def post_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetAnnouncementList()")
    results = cursor.fetchall()
    context = {"post_list": results}
    code = request.POST.get('DiscountCode')
    print('code', code)
    return render(request, "adminpanel/post/postlist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def post_operation(request, id=0):
    cursor = connection.cursor()
    if request.method == "GET":
        if id == 0:
            posts = PostTypeForm()
        else:
            try:
                cursor.callproc('GetAnnouncementPostById', [id])
                posts = cursor.fetchone()
                print('posts', posts)
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()

        return render(request, "adminpanel/post/postoperation.html", {'form': posts})
    else:
        userid = int(request.user.id)
        Title1 = request.POST.get("Title1")
        Title2 = request.POST.get("Title2")
        Description = request.POST.get("Description")

        if id == 0:
            form = PostTypeForm(request.POST)
            data = {"Announcement_Id": "0", "Title1": Title1, "Title2": Title2, "Description": Description}
            dataInString = json.dumps(data)
            cursor.callproc('InsertUpdateActivityLog', [dataInString, 1, userid])
        else:
            posts = AnnouncementPost.objects.get(pk=id)
            form = PostTypeForm(request.POST, instance=posts)
            data = {"Announcement_Id": id, "Title1": Title1, "Title2": Title2, "Description": Description}
            dataInString = json.dumps(data)
            cursor.callproc('InsertUpdateActivityLog', [dataInString, 2, userid])
        if form.is_valid():
            form.save()
        return redirect('/Post')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def post_delete(request, id):
    cursor = connection.cursor()
    userid = int(request.user.id)
    Title1 = request.POST.get("Title1")
    Title2 = request.POST.get("Title2")
    Description = request.POST.get("Description")
    data = {"Announcement_Id": id, "Title1": Title1, "Title2": Title2, "Description": Description}
    dataInString = json.dumps(data)
    posts = AnnouncementPost.objects.get(pk=id)
    cursor.callproc('InsertUpdateActivityLog', [dataInString, 2, userid])
    posts.delete()
    return redirect('/Post')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def activitylog_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetActivityLogList()")
    results = cursor.fetchall()
    print('in activity log list')
    print(results)
    context = {"activitylog_list": results}
    return render(request, "adminpanel/activitylog/activityloglist.html", context)

@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])  
def config_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetConfigurationList()")
    results = cursor.fetchall()
    context = {"config_list": results}
    return render(request, "adminpanel/configuration/configurationlist.html", context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def discount_operation(request, id=0):
    if request.method == "GET":
        if id == 0:
            discount = DiscountTypeForm()
        else:
            # disc = DiscountType.objects.get(pk=id)
            # form = DiscountTypeForm(instance=disc)
            try:
                cursor = connection.cursor()
                cursor.callproc('GetDiscountTypeById', [id])
                discount = cursor.fetchone()
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/discount/discountoperation.html", {'form': discount})
    else:
        if id == 0:
            form = DiscountTypeForm(request.POST)
            # log(user=request.user, action="Add Discount", extra={"DiscountCode":})
        else:
            disc = DiscountType.objects.get(pk=id)
            form = DiscountTypeForm(request.POST, instance=disc)
        try:
            if form.is_valid():
                form.save()
            else:
                print(form.errors)
        except OperationalError as e:
            print(format(e))
        return redirect('/Discount')

def config_operation(request, id=0):
    if request.method == "GET":
        if id == 0:
            config = ConfigurationForm()
        else:
            # disc = DiscountType.objects.get(pk=id)
            # form = DiscountTypeForm(instance=disc)
            try:
                cursor = connection.cursor()
                cursor.callproc('GetConfigurationById', [id])
                config = cursor.fetchone()
            except ConnectionError as e:
                print('ERROR IS: ')
                print(format(e))
            finally:
                cursor.close()
        return render(request, "adminpanel/configuration/configurationoperation.html", {'form': config})
    else:
        if id == 0:
            # log(user=request.user, action="Add Discount", extra={"DiscountCode":})
            form = ConfigurationForm(request.POST, request.FILES)
        else:
            config = Configuration.objects.get(pk=id)
            form = ConfigurationForm(request.POST, request.FILES, instance=config)
        try:
            if form.is_valid():
                form.save()
            else:
                print(form.errors)
        except OperationalError as e:
            print(format(e))
        return redirect('/Configuration')


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def discount_delete(request, id):
    disc = DiscountType.objects.get(pk=id)
    disc.delete()
    return redirect('/Discount')

def orderdetailslist(request):
    cursor = connection.cursor()
    cursor.execute("call GetClientOrderDetailsList()")
    results = cursor.fetchall()
    context = {"orderdetails": results}
    print('order list:')
    print(results)
    return render(request, "adminpanel/customize/manageorderlist.html", context)


def orderdetails_update(request, id=0):
    if request.method == "GET":
        try:
            cursor = connection.cursor()
            cursor.callproc('GetClientOrderDetailsById', [id])
            orderdetails = cursor.fetchone()
        except ConnectionError as e:
            print('ERROR IS: ')
            print(format(e))
        finally:
            cursor.close()
        return render(request, "adminpanel/customize/manageorderedit.html", {'orderdetail': orderdetails})
    else:
        config = Configuration.objects.get(pk=id)
        form = ConfigurationForm(request.POST, instance=config)
        try:
            cursor = connection.cursor()
            cursor.callproc('UpdateClientOrderDetailsById', [id])
            orderdetails = cursor.fetchone()
        except ConnectionError as e:
            print('ERROR IS: ')
            print(format(e))
        finally:
            cursor.close()
        return redirect('/OrderDetails')

@login_required(login_url='Login')
def admin_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetAdminList()")
    results = cursor.fetchall()
    context = {"admin_list": results}
    return render(request, "adminpanel/admin/adminlist.html", context)

@login_required(login_url='Login')
def admin_operation(request, id=0):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        try:
            if form.is_valid():
                str = 0
                cursor = connection.cursor()
                letters_and_digits = string.ascii_letters + string.digits
                password1 = ''.join((random.choice(letters_and_digits) for i in range(8)))
                firstname = request.POST.get("First_Name")
                lastname = request.POST.get("Last_Name")
                email = form.cleaned_data.get("Email")
                username=email
                phone=form.cleaned_data.get("Phone_No")
                gender=form.cleaned_data.get("Gender")
                password = make_password(password1)
                cursor.callproc('InsertNewAdmin',
                                [firstname, username, lastname, password, email,phone,gender])
                print(password1)
                subject = 'Welcome to Prolongevity.'
                fromEmail = settings.EMAIL_HOST_USER
                to_list = [form.cleaned_data.get("Email")]
                try:
                    html_content = render_to_string("message1.html", {'username': username,'password1':password1})
                    text_content = strip_tags(html_content)

                    emailsend = EmailMultiAlternatives(
                        subject,
                        text_content,
                        fromEmail,
                        to_list
                    )
                    emailsend.attach_alternative(html_content, "text/html")
                    conncheck = emailsend.send()
                except Exception as e:
                    print(type(e))
                    messages.error(request, "There is some issue while creating account for " + username)
                messages.success(request, "Account created for" + username)
                return redirect('AdminList')
            else:
                print('error')
                print(form.errors)
                print(form.error_messages)
        except Exception as e:
            print('Error Is:')
    context = {'form': form}
    return render(request, 'adminpanel/admin/adminoperation.html', context)


@login_required(login_url='Login')
def admin_delete(request, id):
    cursor = connection.cursor()
    cursor.callproc('DeleteAdminUser',[id])
    return redirect('/AdminList')

@login_required(login_url='Login')
def superadmin_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetSuperAdminList()")
    results = cursor.fetchall()
    context = {"superadmin_list": results}
    return render(request, "adminpanel/superadmin/superadminlist.html", context)

@login_required(login_url='Login')
def superadmin_operation(request, id=0):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        try:
            if form.is_valid():
                str = 0
                cursor = connection.cursor()
                cursor.callproc('GetConfigurationById', [id])
                config = cursor.fetchone()
        except ConnectionError as e:
            print('ERROR IS: ')
            print(format(e))
        finally:
            cursor.close()
        return render(request, "adminpanel/configuration/configurationoperation.html", {'form': config})
    else:
        if id == 0:
            form = ConfigurationForm(request.POST, request.FILES)
        else:
            config = Configuration.objects.get(pk=id)
            form = ConfigurationForm(request.POST, request.FILES, instance=config)
            letters_and_digits = string.ascii_letters + string.digits
            password1 = ''.join((random.choice(letters_and_digits) for i in range(8)))
            firstname = request.POST.get("First_Name")
            lastname = request.POST.get("Last_Name")
            email = form.cleaned_data.get("Email")
            username=email
            phone=form.cleaned_data.get("Phone_No")
            gender=form.cleaned_data.get("Gender")
            password = make_password(password1)

            cursor.callproc('InsertNewSuperAdmin',
                            [firstname, username, lastname, password, email,phone,gender])
            print(password1)
            subject = 'Thank you for your registration.'
            fromEmail = settings.EMAIL_HOST_USER
            to_list = [form.cleaned_data.get("Email")]
            try:
                html_content = render_to_string("message1.html", {'username': username,'password1':password1})
                text_content = strip_tags(html_content)

                emailsend = EmailMultiAlternatives(
                    subject,
                    text_content,
                    fromEmail,
                    to_list
                )
                emailsend.attach_alternative(html_content, "text/html")
                emailsend.send()
            except Exception as e:
                print('Error in sending email while registration')
                messages.error(request, "There is some issue while creating account for " + username)
            messages.success(request, "Account created for" + username)
            return redirect('superadminList')
        return render(request, 'adminpanel/superadmin/superadminoperation.html', context)


@login_required(login_url='Login')
def superadmin_delete(request, id):
    cursor = connection.cursor()
    cursor.callproc('DeleteSuperAdminUser',[id])
    return redirect('/superadminList')

@login_required(login_url='Login')
def practitioner_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetPractitionerList()")
    results = cursor.fetchall()
    context = {"practitioner_list": results}
    return render(request, "adminpanel/practitioner/practitionerlist.html", context)

@login_required(login_url='Login')
def practitioner_operation(request, id=0):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                str = 0
                cursor = connection.cursor()
                letters_and_digits = string.ascii_letters + string.digits
                password1 = ''.join((random.choice(letters_and_digits) for i in range(8)))
                firstname = request.POST.get("First_Name")
                lastname = request.POST.get("Last_Name")
                email = form.cleaned_data.get("Email")
                username=email
                phone=form.cleaned_data.get("Phone_No")
                gender=form.cleaned_data.get("Gender")
                password = make_password(password1)

                cursor.callproc('InsertNewPractitioner',
                                [firstname, username, lastname, password, email,phone,gender])

                subject = 'Thank you for your registration.'
                fromEmail = settings.EMAIL_HOST_USER
                to_list = [form.cleaned_data.get("Email")]
                try:
                    html_content = render_to_string("message1.html", {'username': username,'password1':password1})
                    text_content = strip_tags(html_content)

                    emailsend = EmailMultiAlternatives(
                        subject,
                        text_content,
                        fromEmail,
                        to_list
                    )
                    emailsend.attach_alternative(html_content, "text/html")
                    emailsend.send()
                except Exception as e:
                    print('Error in sending email while registration')
                    messages.error(request, "There is some issue while creating account for " + username)
                messages.success(request, "Account created for" + username)
                return redirect('practitionerList')
            else:
                print('error')
                print(form.errors)
        except Exception as e:
            print('Error Is:', str)
    context = {'form': form}
    return render(request, 'adminpanel/practitioner/practitioneroperation.html', context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def manageCurrentOrderDetailsList(request):
    cursor=connection.cursor()
    searchCriteriaValue = request.POST.get("txtSearchForManageOrder")
    category = request.POST.get("searchManageOrder")
    print('searchCriteriaValue', searchCriteriaValue)
    print('category', category)
    cursor.execute("call GetCurrentPlacedAndProcessedOrders()")
    results = cursor.fetchall()
    page = request.GET.get('page', 1)
    paginator = Paginator(results, 10)
    try:
        orderDetails = paginator.page(page)
    except PageNotAnInteger:
        orderDetails = paginator.page(1)
    except EmptyPage:
        orderDetails = paginator.page(paginator.num_pages)
    context = {"currentOrders": orderDetails}
    return render(request, "adminpanel/adminmanagement/manageCurrentOrder.html", context)


def practitioner_delete(request, id):
    cursor = connection.cursor()
    cursor.callproc('DeletePractitionerUser',[id])
    return redirect('/practitionerList')

@login_required(login_url='Login')
def consultant_list(request):
    cursor = connection.cursor()
    cursor.execute("call GetConsultantList()")
    results = cursor.fetchall()
    context = {"consultant_list": results}
    return render(request, "adminpanel/consultant/consultantlist.html", context)

@login_required(login_url='Login')
def consultant_operation(request, id=0):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        try:
            if form.is_valid():
                str = 0
                cursor = connection.cursor()
                letters_and_digits = string.ascii_letters + string.digits
                password1 = ''.join((random.choice(letters_and_digits) for i in range(8)))
                firstname = request.POST.get("First_Name")
                lastname = request.POST.get("Last_Name")
                email = form.cleaned_data.get("Email")
                username=email
                phone=form.cleaned_data.get("Phone_No")
                gender=form.cleaned_data.get("Gender")
                password = make_password(password1)

                cursor.callproc('InsertNewConsultant',
                                [firstname, username, lastname, password, email,phone,gender])

                subject = 'Thank you for your registration.'
                fromEmail = settings.EMAIL_HOST_USER
                to_list = [form.cleaned_data.get("Email")]
                try:
                    html_content = render_to_string("message1.html", {'username': username,'password1':password1})
                    text_content = strip_tags(html_content)

                    emailsend = EmailMultiAlternatives(
                        subject,
                        text_content,
                        fromEmail,
                        to_list
                    )
                    emailsend.attach_alternative(html_content, "text/html")
                    emailsend.send()
                except Exception as e:
                    print('Error in sending email while registration')
                    messages.error(request, "There is some issue while creating account for " + username)
                messages.success(request, "Account created for" + username)
                return redirect('consultantList')
            else:
                print('error')
                print(form.errors)
                print(form.error_messages)
        except Exception as e:
            print('Error Is:')
    context = {'form': form}
    return render(request, 'adminpanel/consultant/consultantoperation.html', context)


@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def manageCurrentOrderShip(request, id):
    order = Order.objects.get(Order_Id=id)
    customer = Customer.objects.get(Customer_Id=order.Customer_id)
    order.OrderStatus_id = 3
    order.save()

    subject = 'Order Shipped for Order# ' + str(id)
    fromEmail = settings.EMAIL_HOST_USER
    to_list = [customer.Email]
    customerName = customer.First_Name + ' ' + customer.Last_Name
    html_content = render_to_string("sendemail/OrderShipment.html", {'customerName': customerName})
    text_content = strip_tags(html_content)
    email_send = EmailMultiAlternatives(
        subject,
        text_content,
        fromEmail,
        to_list
    )
    message = ""
    email_send.attach_alternative(html_content, "text/html")
    try:
        email_send.send()
        message = "Success"
    except Exception as e:
        print('Error Is:', str(e))
        message = "Failed"
    print('email sent from adminpanel/adminview/manageCurrentOrderShip')

def consultant_delete(request, id):
    cursor = connection.cursor()
    cursor.callproc('DeleteConsultantUser',[id])
    return redirect('/consultantList')

    return redirect('/ManageOrder')

@login_required(login_url='Login')
def viewCalendar(request):
    userId=request.user.id
    cursor1 = connection.cursor()
    cursor1.execute("call viewSlots()")
    results = cursor1.fetchall()
    cursor1.callproc('viewAvailableSlots',[userId])
    resultslot = cursor1.fetchall()
    resultslot1=list(resultslot)
    res = [list(ele) for ele in resultslot1]
    for iterator in range(len(res)):
        res[iterator][4]=res[iterator][4].isoformat()
        res[iterator][5]=res[iterator][5].isoformat()
    context = {"confirmAvailability": results, "events": res}
    cursor1.callproc('viewBookedSlots',[userId])
    resultslotbooked = cursor1.fetchall()
    if resultslotbooked:
        resultslot1booked=list(resultslotbooked)
        resbooked = [list(ele) for ele in resultslot1booked]
        for iterator in range(len(resbooked)):
            resbooked[iterator][4]=resbooked[iterator][4].isoformat()
            resbooked[iterator][5]=resbooked[iterator][5].isoformat()
        context.update({'checkevent':resbooked})
    return render(request, "practitionerpanel/Calendar/calendar_home.html",context)

@login_required(login_url='Login')
@CustomDecorator.allowed_users(allowed_roles=['superadmin', 'admin'])
def manageCurrentOrderProcess(request, id):
    order = Order.objects.get(Order_Id=id)
    order.OrderStatus_id = 2
    order.save()
    return redirect('/ManageOrder')

def confirmAvailability(request):
    userId=request.user.id
    cursor1 = connection.cursor()
    cursor1.execute("call viewSlots()")
    results = cursor1.fetchall()
    cursor1.callproc('viewAvailableSlots',[userId])
    resultslot = cursor1.fetchall()
    context={'confirmAvailability1':results}
    if request.method=='POST':
        print("Function working")
        cursor = connection.cursor()
        availableDate=request.POST.get('slot_date')
        checkedvalue=request.POST.getlist('slot_time[]')
        for slot in checkedvalue:
            cursor.callproc('checkSlot',[availableDate,slot,userId])
            result1=cursor.fetchall()
            if result1:
                if result1[0][2] == 1:
                    continue
                else:
                    slotid=result1[0][0]
                    cursor.callproc('updateSlot',[slotid])
            else:
                cursor.callproc('bookSlot',[availableDate,slot,userId])
        return redirect(viewCalendar)
    else: 
        return render(request, "practitionerpanel/Calendar/bookavailabilityform.html",context)


@login_required(login_url='Login')
def calendarSlot_update(request, id):
    userId=request.user.id
    cursor = connection.cursor()
    cursor.execute("call viewSlots()")
    results = cursor.fetchall()
    cursor.callproc('getDate',[id])
    results1 = cursor.fetchall()
    mydat=results1[0][0]
    datvalue=mydat.strftime("%Y-%m-%d")
    print(datvalue)
    cursor.callproc('getdateslots',[results1,userId])
    results2=[i[0] for i in cursor.fetchall()]
    if request.method=='POST':
        cursor = connection.cursor()
        cursor.callproc('deleteOldSlot',[results1,userId])
        availableDate=request.POST.get('slot_date')
        checkedvalue=request.POST.getlist('slot_time[]')
        for slot in checkedvalue:
            cursor.callproc('checkSlot',[availableDate,slot,userId])
            result1=cursor.fetchall()
            if result1:
                if result1[0][2] == 1:
                    continue
                else:
                    slotid=result1[0][0]
                    cursor.callproc('updateSlot',[slotid])
            else:
                cursor.callproc('bookSlot',[availableDate,slot,userId])
        return redirect('/calendarSlots')
    return render(request, "practitionerpanel/Calendar/updateavailabilityform.html", {"viewSlots1": results, "datevalue":datvalue, "slotvalue":results2})

@login_required(login_url='Login')
def calendar_unavailable(request):
    print('working')
    id1=request.POST.get("id",None)
    print(id1)
    cursor = connection.cursor()
    cursor.callproc('DeleteSlot',[id1])
    data = {}
    return JsonResponse({'success':True})

@login_required(login_url='Login')
def calendar_cancelAppointment(request):
    id1=request.POST.get("id",None)
    print(id1)
    cursor = connection.cursor()
    cursor.callproc('DeleteAppointment',[id1])
    data = {}
    return JsonResponse({'success':True})

@login_required(login_url='Login')
def calendar_cancelAppointment1(request,id):
    id1=id
    print(id1)
    cursor = connection.cursor()
    cursor.callproc('DeleteAppointment',[id1])
    return redirect('/home')

@login_required(login_url='Login')
def calendar_addAvailability(request):
    print('working')
    userId=request.user.id
    cursor1 = connection.cursor()
    dateval=request.POST.get('slot_date')
    startTimeStr=request.POST.get('slotstarttime')
    endTimeStr=request.POST.get('slotendtime')
    print(startTimeStr)
    print(endTimeStr)
    startTime=dateutil.parser.isoparse(startTimeStr)
    endTime=dateutil.parser.isoparse(endTimeStr)
    delta = timedelta(minutes=30)
    five_min_timestamps = []
    date_x = startTime
    while date_x < endTime:
        five_min_timestamps.append(datetime.time(date_x))
        date_x += timedelta(minutes=30)
    cursor1.execute("call viewSlots()")
    results = cursor1.fetchall()
    slot_times= []
    slot_id_list=[]
    for res in results:
        slot_times.append(datetime.time(res[3]))
    for i in range(24):
        if slot_times[i] in five_min_timestamps:
            slotidkey=i+1
            slot_id_list.append(str(slotidkey))
    for slot in slot_id_list:
            cursor1.callproc('checkSlot',[dateval,slot,userId])
            result1=cursor1.fetchall()
            if result1:
                if result1[0][2] == 1:
                    continue
                else:
                    slotid=result1[0][0]
                    cursor1.callproc('updateSlot',[slotid])
            else:
                cursor1.callproc('bookSlot',[dateval,slot,userId])
    return redirect('/calendarSlots')

@login_required(login_url='Login')
def calendar_rescheduleAppointment(request):
    cursor=connection.cursor()
    userId=request.user.id
    if request.method=='POST':
        return redirect(viewCalendar)
        dateval = request.POST.get('reschedule_slot_date')
        rescheduleStart = request.POST.get('reschedule_start_slot')
        rescheduleEnd = request.POST.get('reschedule_end_slot')
        clientid=request.POST.get('reschedule_client_id')
        id=request.POST.get('reschedule_slot_id')
        cursor.callproc('Reschedule_DeleteSlot',[id])
        res=cursor.fetchall()
        pracid=res[0][0]
        cursor.callproc('GetCustomerDetailsById',[clientid])
        clientdetails=cursor.fetchall()
        clientemail=clientdetails[0][3]
        clientname=clientdetails[0][1]+''+clientdetails[0][2]
        print(clientname)
        startTimeStr=dateval+'T'+rescheduleStart+':00Z'
        endTimeStr=dateval+'T'+rescheduleEnd+':00Z'
        startTime=dateutil.parser.isoparse(startTimeStr)
        endTime=dateutil.parser.isoparse(endTimeStr)
        five_min_timestamps = []
        date_x = startTime
        while date_x < endTime:
            five_min_timestamps.append(datetime.time(date_x))
            date_x += timedelta(minutes=30)
        cursor.execute("call viewSlots()")
        results = cursor.fetchall()
        slot_times= []
        slot_id_list=[]
        for res in results:
            slot_times.append(datetime.time(res[3]))
        for i in range(24):
            if slot_times[i] in five_min_timestamps:
                slotidkey=i+1
                slot_id_list.append(str(slotidkey))
        for slot in slot_id_list:
                cursor.callproc('checkSlot',[dateval,slot,userId])
                result1=cursor.fetchall()
                if result1:
                    if result1[0][2] == 1:
                        continue
                    else:
                        slotid=result1[0][0]
                        cursor.callproc('updateSlot',[slotid])
                else:
                    cursor.callproc('bookSlot',[dateval,slot,userId])
        slotid=[]
        for timestart in five_min_timestamps:
            cursor.callproc('getSlotId',[timestart])
            slotid.append(cursor.fetchall())
        cursor.callproc('bookappointment',[clientid,pracid,datetime.date(startTime),datetime.time(startTime),datetime.time(endTime)])
        appointmentid=cursor.fetchall()
        for idkey in slotid:
            cursor.callproc('updateCalendarSlot',[datetime.date(startTime),idkey[0][0],pracid,appointmentid])
        cal = Calendar()
        cal.add('prodid', '-//My calendar product//mxm.dk//')
        cal.add('version', '2.0')
        cal.add('method','REQUEST')
        eventstart=datetime.fromisoformat(startTimeStr.replace('Z', ''))
        eventend=datetime.fromisoformat(endTimeStr.replace('Z', ''))
        print(eventstart)
        print(eventend)
        event = Event()
        event.add('summary', 'Appointment Rescheduled')
        event['dtstart'] = startTimeStr.replace('-','').replace(':','')
        event['dtend'] = endTimeStr.replace('-','').replace(':','')
        event['uid'] = appointmentid[0][0]
        event['method'] = 'REQUEST'
        organizer = vCalAddress('MAILTO:%s' % settings.EMAIL_HOST_USER)
        organizer.params['cn'] = vText('Prolongevity')
        organizer.params['role'] = vText('Practitioner')
        event['organizer'] = organizer
        event['location'] = vText('St Albans')
        # attendee = vCalAddress('MAILTO:%s' % clientemail)
        attendee = vCalAddress('MAILTO:anujpalimkar@gmail.com')
        attendee.params['cn'] = vText('%s' % clientname)
        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
        attendee.params['RSVP'] = "TRUE"
        attendee.params["PARTSTAT"] = "NEEDS-ACTION" 
        event.add('attendee', attendee, encode=0)
        cal.add_component(event)
        subject = 'Rescheduled- Your Appointment '
        fromEmail = settings.EMAIL_HOST_USER
        to_list = ['anujpalimkar@gmail.com']
        calstring=str(cal.to_ical(),'utf-8')
        print(calstring)
        print(cal.to_ical())
        try:
            text_content = 'Your appointment with prolongevity is rescheduled'

            emailsend = EmailMultiAlternatives(
                subject,
                text_content,
                fromEmail,
                to_list
            )
            emailsend.attach('calcheck.ics', cal.to_ical(),'text/calendar')
            # emailsend.attach_alternative(cal.to_ical(), "text/calendar; method=REQUEST; charset=\"UTF-8\"")
            # emailsend.content_subtype = 'calendar'
            emailsend.send()
        except Exception as e:
            print('Error in sending email while registration'+str(e))
    return redirect(viewCalendar)

@login_required(login_url='Login')
def calendar_giveRecommendation(request):
    print('working')
    cursor=connection.cursor()
    if request.method == 'POST':
        clientid=request.POST.get('recommendation_client_id')
        apptid=request.POST.get('recommendation_slot_id')
        diagnosis=request.POST.get('recommendation_diagnosis')
        recommendation=request.POST.get('recommendation_dietplan')
        cursor.callproc('updateAppointment',[apptid])
        result=cursor.fetchall()
        pracid=result[0][0]
        cursor.callproc('addRecommendation',[apptid,clientid,pracid,diagnosis,recommendation])
        recommendationid=cursor.fetchall()
        cursor.callproc('updateAppointment_addRecommendation',[apptid,recommendationid])
        cursor.callproc('GetCustomerDetailsById',[clientid])
        clientdetails=cursor.fetchall()
        clientemail=clientdetails[0][3]
        clientname=clientdetails[0][1]+''+clientdetails[0][2]
        subject = 'Appointment Report from Prolongevity'
        fromEmail = settings.EMAIL_HOST_USER
        to_list = [clientemail]
        try:
            text_content = 'Please find detailed report for your Appointment.'

            emailsend = EmailMultiAlternatives(
                subject,
                text_content,
                fromEmail,
                to_list
            )
            emailsend.attach_alternative(text_content, "text/html")
            pdf = render_to_pdf('recommendation.html', {'Appointmentdetail':result,'clientdetail':clientname,'diagnosis':diagnosis,'recommendation':recommendation})
            emailsend.attach('Recommendation_'+result[0][1].strftime("%m/%d/%Y") +'.pdf', pdf, 'file/pdf')
            emailsend.send()
        except Exception as e:
            print('Error in sending email while registration'+str(e))
        return redirect(viewCalendar)


@login_required(login_url='Login')
def calendar_viewHistory(request):
    if request.method=='POST':
        cursor=connection.cursor()
        id1=request.POST.get("id",None)
        cursor.callproc('viewClientRecommendation',[id1])
        result=cursor.fetchall()
        clientname=result[0][2]
        print(clientname)
        html = render_to_string('practitionerpanel/Calendar/viewHistory.html',{'recommendationhistory':result,'clientname':clientname})
        return HttpResponse(html)

@login_required(login_url='Login')
def viewUpcomingAppointment(request):
    userId=request.user.id
    cursor1 = connection.cursor()
    cursor1.callproc('viewBookedSlots',[userId])
    context={}
    resultslotbooked = cursor1.fetchall()
    if resultslotbooked:
        context.update({'eventbooked':resultslotbooked})
    return render(request, "practitionerpanel/viewUpcomingAppointment.html",context)

@login_required(login_url='Login')
def viewAppointmentHistory(request,b=None):
    userId=request.user.id
    cursor1 = connection.cursor()
    cursor1.callproc('practitioner_viewRecommendationHistory',[userId])
    context={}
    resultslotbooked = cursor1.fetchall()
    if resultslotbooked:
        context.update({'eventbooked':resultslotbooked})
    if b:
        context.update({'b':b})
        print(b)
    return render(request, "practitionerpanel/viewAppointmentHistory.html",context)

@login_required(login_url='Login')
def updateRecommendation(request):
    if request.method == 'POST':
        cursor1=connection.cursor()
        clientid=request.POST.get('recommendation_client_id')
        recommendid=request.POST.get('recommendation_slot_id')
        diagnosis=request.POST.get('recommendation_diagnosis')
        recommendation=request.POST.get('recommendation_dietplan')
        cursor1.callproc('GetCustomerDetailsById',[clientid])
        clientdetails=cursor1.fetchall()
        clientemail=clientdetails[0][3]
        clientname=clientdetails[0][1]+''+clientdetails[0][2]
        cursor1.callproc('updateRecommendation',[recommendid,diagnosis,recommendation])
        result=cursor1.fetchall()
        subject = 'Appointment Report Updated from Prolongevity'
        fromEmail = settings.EMAIL_HOST_USER
        to_list = [clientemail]
        try:
            text_content = 'Please find updated report for your Appointment.'

            emailsend = EmailMultiAlternatives(
                subject,
                text_content,
                fromEmail,
                to_list
            )
            emailsend.attach_alternative(text_content, "text/html")
            pdf = render_to_pdf('recommendation.html', {'Appointmentdetail':result,'clientdetail':clientname,'diagnosis':diagnosis,'recommendation':recommendation})
            emailsend.attach('Recommendation_Updated'+result[0][1].strftime("%m/%d/%Y") +'.pdf', pdf, 'file/pdf')
            emailsend.send()
        except Exception as e:
            print('Error in sending email while registration'+str(e))
        return render(request,"practitionerpanel/updateConfirmationDialog.html")
