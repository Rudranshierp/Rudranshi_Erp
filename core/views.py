from .utils import check_subscription
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .models import Invoice, InvoiceItem, Company, UserCompanyRole, Product, Customer, ProductCategory
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .serializers import InvoiceSerializer


# ================= AUTH PAGES =================

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def pricing(request):
    return render(request, 'pricing.html')

    
def logout_page(request):
    logout(request)
    return redirect('/')


def dashboard_page(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    # 🔥 GET COMPANY
    company = Company.objects.filter(user=request.user).first()

    # 🔥 BASE QUERY
    invoices = Invoice.objects.all().order_by('-id')

    # 🔥 DATE FILTER (NEW)
    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        invoices = invoices.filter(created_at__date__range=[start, end])

    # 🔥 SUMMARY
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
    total_gst = invoices.aggregate(total=Sum('gst_amount'))['total'] or 0

    # 🔥 MONTHLY SALES (CHART DATA)
    monthly = (
        invoices.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    labels = []
    data = []

    for m in monthly:
        labels.append(m['month'].strftime('%b'))
        data.append(float(m['total'] or 0))

    # 🔥 PIE DATA (PAYMENT TYPE DEMO SAFE)
    pie_data = [40, 30, 30]  # later real payment logic laga sakte ho

    # 🔥 RECENT ACTIVITY (NEW)
    activities = invoices[:5]

    # 🔥 ACTIVE CUSTOMERS (SAFE)
    active_customers = Customer.objects.filter(company=company).count() if company else 0
    sub = UserSubscription.objects.filter(user=request.user).first()

    sub_active = False

    if sub and sub.is_active and sub.end_date >= date.today():
        sub_active = True

    context = {
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'total_gst': total_gst,
        'invoices': invoices,
        'company': company,

        # 🔥 NEW ADDITIONS
        'labels': labels,
        'data': data,
        'pie_data': pie_data,
        'activities': activities,
        'active_customers': active_customers,
        'sub_active': sub_active,
    }

    return render(request, 'dashboard.html', context)


def create_invoice_page(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    # 🔥 GET DATA (for form)
    products = Product.objects.all()
    companies = Company.objects.all()

    if request.method == 'POST':

        product_list = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        gsts = request.POST.getlist('gst[]')

        # 🔥 FIXED (POST capital)
        company_id = request.POST.get('company_id')

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return redirect('/dashboard/')

        # 🔥 CREATE INVOICE
        invoice = Invoice.objects.create(
            company=company,
            description="Multi item invoice"
        )

        # 🔥 ITEMS LOOP
        for i in range(len(product_list)):
            try:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product_name=product_list[i],
                    quantity=int(quantities[i]),
                    price=float(prices[i]),
                    gst_percent=float(gsts[i])
                )
            except:
                pass  # crash avoid

        invoice.save()

        return redirect('/dashboard/')

    return render(request, 'create_invoice.html', {
        'products': products,
        'companies': companies
    })


def subscribe(request, plan_id, billing_type):

    plan = SubscriptionPlan.objects.get(id=plan_id)

    days = 30 if billing_type == "monthly" else 180 if billing_type == "half_yearly" else 365

    end_date = date.today() + timedelta(days=days)

    UserSubscription.objects.update_or_create(
        user=request.user,
        defaults={
            "plan": plan,
            "billing_type": billing_type,
            "end_date": end_date,
            "is_active": True
        }
    )

    return redirect('/dashboard/')
    
def view_invoice_page(request, id):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    try:
        invoice = Invoice.objects.get(id=id)
    except Invoice.DoesNotExist:
        return redirect('/dashboard/')

    return render(request, 'view_invoice.html', {
        'invoice': invoice
    })


# ================= USER ROLE =================

def get_user_company_role(request):
    try:
        return UserCompanyRole.objects.get(user=request.user)
    except UserCompanyRole.DoesNotExist:
        return None


def get_company(request):
    user_role = get_user_company_role(request)
    return user_role.company if user_role else None


def get_user_role(request):
    user_role = get_user_company_role(request)
    return user_role.role if user_role else None


# ================= CREATE =================

def create_invoice(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)
    role = get_user_role(request)

    if not company:
        return Response({"error": "Company not found"}, status=404)

    if role not in ['admin', 'accountant']:
        return Response({"error": "Permission denied"}, status=403)

    serializer = InvoiceSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(company=company)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


# ================= LIST =================

def get_invoices(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)

    if not company:
        return Response({"error": "Company not found"}, status=404)

    search = request.GET.get('search')
    page = request.GET.get('page', 1)

    invoices = Invoice.objects.filter(company=company)

    if search:
        invoices = invoices.filter(
            Q(description__icontains=search) |
            Q(invoice_number__icontains=search)
        )

    paginator = Paginator(invoices, 5)
    page_obj = paginator.get_page(page)

    serializer = InvoiceSerializer(page_obj, many=True)

    return Response({
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "total_records": paginator.count,
        "data": serializer.data
    })


# ================= GET ONE =================

def get_invoice(request, id):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)

    if not company:
        return Response({"error": "Company not found"}, status=404)

    try:
        invoice = Invoice.objects.get(id=id, company=company)
    except Invoice.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = InvoiceSerializer(invoice)
    return Response(serializer.data)


# ================= UPDATE =================

def update_invoice(request, id):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)
    role = get_user_role(request)

    if not company:
        return Response({"error": "Company not found"}, status=404)

    if role != 'admin':
        return Response({"error": "Only admin can update"}, status=403)

    try:
        invoice = Invoice.objects.get(id=id, company=company)
    except Invoice.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = InvoiceSerializer(invoice, data=request.data)

    if serializer.is_valid():
        serializer.save(company=company)
        return Response(serializer.data)

    return Response(serializer.errors, status=400)


# ================= DELETE =================

def delete_invoice(request, id):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)
    role = get_user_role(request)

    if not company:
        return Response({"error": "Company not found"}, status=404)

    if role != 'admin':
        return Response({"error": "Only admin can delete"}, status=403)

    try:
        invoice = Invoice.objects.get(id=id, company=company)
    except Invoice.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    invoice.delete()
    return Response({"message": "Deleted successfully"})


# ================= PDF =================

def download_invoice_pdf(request, id):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    import os
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    company = get_company(request)

    try:
        invoice = Invoice.objects.get(id=id, company=company)
    except Invoice.DoesNotExist:
        return redirect('/dashboard/')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        leftMargin=10,
        rightMargin=10,
        topMargin=10,
        bottomMargin=10
    )

    styles = getSampleStyleSheet()

    normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=9)
    title_style = ParagraphStyle('title', parent=styles['Title'], alignment=1)

    elements = []

    PAGE_WIDTH = 570
    HALF = PAGE_WIDTH / 2

    # ================= LOGO =================
    try:
        logo_path = os.path.join("core", "static", "logo.png")
        logo = Image(logo_path, width=55, height=55)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 5))
    except:
        pass

    # ================= TITLE =================
    elements.append(Paragraph("<b>TAX INVOICE</b>", title_style))
    elements.append(Spacer(1, 8))

    # ================= ITEMS TABLE =================
    data = [["Sl", "Description", "HSN", "Qty", "Rate", "Amount"]]

    for i, item in enumerate(invoice.items.all(), start=1):
        total = item.quantity * item.price
        data.append([
            str(i),
            item.product_name,
            "4810",
            str(item.quantity),
            str(item.price),
            str(total)
        ])

    items_table = Table(data, colWidths=[30, 170, 60, 50, 90, 110])
    items_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1.2, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))

    # ================= GST =================
    total_gst = invoice.gst_amount
    cgst = total_gst / 2
    sgst = total_gst / 2

    gst_table = Table([
        ["Tax Type", "Amount"],
        ["CGST", str(round(cgst, 2))],
        ["SGST", str(round(sgst, 2))],
        ["Total GST", str(round(total_gst, 2))]
    ], colWidths=[140, 90])

    gst_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1.2, colors.black),
    ]))

    # ================= MAIN GRID =================
    main = Table([

        # HEADER
        [
            Paragraph(f"<b>{invoice.company.name}</b><br/>GSTIN: 08XXXXX<br/>Jaipur, Rajasthan", normal),
            Paragraph(f"Invoice No: {invoice.invoice_number}<br/>Date: {invoice.created_at.strftime('%d-%m-%Y')}", normal)
        ],

        # BUYER / CONSIGNEE
        [
            Paragraph("<b>Buyer (Bill To)</b><br/>Customer Name<br/>Address<br/>GSTIN: XXXXX", normal),
            Paragraph("<b>Consignee (Ship To)</b><br/>Customer Name<br/>Address<br/>GSTIN: XXXXX", normal)
        ],

        # ITEMS FULL WIDTH
        [items_table, ""],

        # GST + TOTAL
        [
            gst_table,
            Paragraph(
                f"""
                Subtotal: Rs. {invoice.total_amount}<br/>
                <b>Final Amount: Rs. {invoice.final_amount}</b><br/>
                Amount in Words: Rupees XXXX Only
                """,
                normal
            )
        ],

        # BANK + SIGN
        [
            Paragraph("<b>Bank Details</b><br/>Bank: XYZ Bank<br/>A/C: XXXXX<br/>IFSC: XXXXX", normal),
            Paragraph("Authorised Signatory", normal)
        ],

        # DECLARATION FULL WIDTH
        [
            Paragraph("Declaration: We declare that this invoice is true.", normal),
            ""
        ]

    ], colWidths=[HALF, HALF])

    main.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1.2, colors.black),

        # ITEMS FULL WIDTH
        ('SPAN', (0,2), (1,2)),

        # DECLARATION FULL WIDTH
        ('SPAN', (0,5), (1,5)),

        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))

    elements.append(main)

    doc.build(elements)
    return response

    # ================= PRODUCT =================

def product_list(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)
    products = Product.objects.filter(company=company)

    return render(request, 'product_list.html', {
        'products': products
    })


def create_product(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)

    if request.method == 'POST':
        Product.objects.create(
            company=company,
            name=request.POST.get('name'),
            price=request.POST.get('price'),
            gst_percent=request.POST.get('gst'),
            category_id=request.POST.get('category')
        )
        return redirect('/products/')

    categories = ProductCategory.objects.filter(company=company)

    return render(request, 'create_product.html', {
        'categories': categories
    })


def customer_list(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)
    customers = Customer.objects.filter(company=company)

    return render(request, 'customers.html', {
        'customers': customers
    })


def create_customer(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)

    if request.method == 'POST':
        Customer.objects.create(
            company=company,
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
        )
        return redirect('/customers/')

    return render(request, 'create_customer.html')


def create_purchase(request):
    if not check_subscription(request.user):
        return Response({"error": "Subscription expired"}, status=403)

    company = get_company(request)

    if request.method == 'POST':
        products = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')

        purchase = Purchase.objects.create(
            company=company,
            supplier_name=request.POST.get('supplier')
        )

        total = 0

        for i in range(len(products)):
            product = Product.objects.get(id=products[i])
            qty = int(quantities[i])
            price = float(prices[i])

            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=qty,
                price=price
            )

            # 🔥 STOCK INCREASE
            product.stock += qty
            product.save()

            total += qty * price

        purchase.total_amount = total
        purchase.save()

        return redirect('/dashboard/')

    products = Product.objects.filter(company=company)

    return render(request, 'create_purchase.html', {
        'products': products
    })