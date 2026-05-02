from django.contrib import admin
from .models import (
    Company,
    UserCompanyRole,
    Invoice,
    InvoiceItem,
    Product,
    ProductCategory,
    Customer,
    Industry,
    SubscriptionPlan,
    UserSubscription
)


# ================= COMPANY =================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'industry', 'gstin', 'created_at')
    search_fields = ('name', 'user__username', 'gstin')
    list_filter = ('industry', 'created_at')
    list_select_related = ('user', 'industry')


# ================= USER ROLE =================
@admin.register(UserCompanyRole)
class UserCompanyRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company', 'role')
    list_filter = ('role', 'company')
    search_fields = ('user__username', 'company__name')
    list_select_related = ('user', 'company')


# ================= INVOICE ITEM INLINE =================
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


# ================= INVOICE =================
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'invoice_number',
        'company',
        'customer',  # 🔥 added
        'total_amount',
        'gst_amount',
        'cgst',
        'sgst',
        'igst',
        'is_interstate',
        'final_amount',
        'created_at'
    )

    list_filter = ('company', 'is_interstate', 'created_at')
    search_fields = ('invoice_number', 'company__name', 'customer__name')
    list_select_related = ('company', 'customer')

    inlines = [InvoiceItemInline]


# ================= INVOICE ITEM =================
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'invoice',
        'product_name',
        'product',  # 🔥 added
        'quantity',
        'price',
        'gst_percent'
    )

    search_fields = ('product_name',)
    list_select_related = ('invoice', 'product')


# ================= PRODUCT =================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'gst_percent', 'stock', 'company', 'created_at')
    search_fields = ('name',)
    list_filter = ('company', 'created_at')
    list_select_related = ('company', 'category')


# ================= PRODUCT CATEGORY =================
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'created_at')
    search_fields = ('name',)
    list_filter = ('company',)
    list_select_related = ('company',)


# ================= CUSTOMER =================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'phone', 'email', 'created_at')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('company',)
    list_select_related = ('company',)


# ================= INDUSTRY =================
@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# ================= SUBSCRIPTION PLAN =================
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'monthly_price',
        'half_yearly_price',
        'yearly_price',
        'max_companies',
        'max_users',
        'created_at'
    )
    search_fields = ('name',)


# ================= USER SUBSCRIPTION =================
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'plan',
        'billing_type',
        'start_date',
        'end_date',
        'is_active'
    )
    list_filter = ('billing_type', 'is_active')
    search_fields = ('user__username', 'plan__name')
    list_select_related = ('user', 'plan')