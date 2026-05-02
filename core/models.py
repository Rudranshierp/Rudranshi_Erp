from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 🔥 IMPORTANT (views imports for your function)
from django.shortcuts import render, redirect


# ================= SUBSCRIPTION PLAN =================
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    monthly_price = models.FloatField()
    half_yearly_price = models.FloatField()
    yearly_price = models.FloatField()
    max_companies = models.IntegerField()
    max_users = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 added

    def __str__(self):
        return self.name


# ================= USER SUBSCRIPTION =================
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)

    BILLING_CHOICES = [
        ('monthly', 'Monthly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ]
    billing_type = models.CharField(max_length=20, choices=BILLING_CHOICES)

    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def is_expired(self):
        return self.end_date < timezone.now().date()  # 🔥 added

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"


# ================= INDUSTRY =================
class Industry(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ================= COMPANY =================
class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    gstin = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 added

    def __str__(self):
        return self.name


# ================= PRODUCT CATEGORY =================
class ProductCategory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 added

    def __str__(self):
        return self.name


# ================= PRODUCT =================
class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=200)
    price = models.FloatField()
    gst_percent = models.FloatField(default=0)

    stock = models.IntegerField(default=0)  # 🔥 added

    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 added

    def __str__(self):
        return self.name


# ================= CUSTOMER =================
class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 added

    def __str__(self):
        return self.name


# ================= INVOICE =================
class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)  # 🔥 added

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    invoice_number = models.CharField(max_length=30, blank=True, null=True)

    total_amount = models.FloatField(default=0)
    gst_amount = models.FloatField(default=0)
    cgst = models.FloatField(default=0)
    sgst = models.FloatField(default=0)
    igst = models.FloatField(default=0)
    is_interstate = models.BooleanField(default=False)
    final_amount = models.FloatField(default=0)

    def save(self, *args, **kwargs):

        if not self.invoice_number:
            last = Invoice.objects.filter(company=self.company).order_by('-id').first()
            last_no = int(last.invoice_number.split('-')[-1]) if last and last.invoice_number else 0
            self.invoice_number = f"{self.company.id}-INV-{str(last_no+1).zfill(4)}"

        total, gst_total = 0, 0

        if self.pk:
            for item in self.items.all():
                total += item.get_total()
                gst_total += item.get_gst_amount()

        self.total_amount = total
        self.gst_amount = gst_total
        self.final_amount = total + gst_total

        if self.is_interstate:
            self.igst = gst_total
            self.cgst = self.sgst = 0
        else:
            self.cgst = gst_total / 2
            self.sgst = gst_total / 2
            self.igst = 0

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['company', 'invoice_number']

    def __str__(self):
        return self.invoice_number


# ================= INVOICE ITEMS =================
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)  # 🔥 added

    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.FloatField()
    gst_percent = models.FloatField(default=0)

    def get_total(self):
        return self.quantity * self.price

    def get_gst_amount(self):
        return (self.get_total() * self.gst_percent) / 100

    def __str__(self):
        return self.product_name


# ================= USER ROLE =================
class UserCompanyRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('accountant', 'Accountant'),
        ('staff', 'Staff'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.company.name} - {self.role}"


# ================= CREATE INVOICE VIEW (UNCHANGED BUT FIXED 🔥) =================
def create_invoice_page(request):
    if not request.user.is_authenticated:
        return redirect('/')

    # 🔥 SaaS SECURITY FIX
    products = Product.objects.filter(company__user=request.user)
    companies = Company.objects.filter(user=request.user)

    if request.method == 'POST':

        product_list = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        gsts = request.POST.getlist('gst[]')

        company_id = request.POST.get('company_id')

        try:
            company = Company.objects.get(id=company_id, user=request.user)
        except Company.DoesNotExist:
            return redirect('/dashboard/')

        invoice = Invoice.objects.create(
            company=company,
            description="Multi item invoice"
        )

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
                pass

        invoice.save()

        return redirect('/dashboard/')

    return render(request, 'create_invoice.html', {
        'products': products,
        'companies': companies
    })


# ================= FUTURE ERP EXTENSION =================
# Customer, Product, Reports, Inventory यहाँ add होंगे