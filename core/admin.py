from django.contrib import admin
from .models import Company, UserCompanyRole, Invoice, InvoiceItem
from .models import Product, ProductCategory   # ✅ FIXED (correct names)


# ================= COMPANY =================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user')
    search_fields = ('name', 'user__username')


# ================= USER ROLE =================
@admin.register(UserCompanyRole)
class UserCompanyRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'company__name')


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
    search_fields = ('invoice_number', 'company__name')

    inlines = [InvoiceItemInline]


# ================= INVOICE ITEM =================
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'invoice',
        'product_name',
        'quantity',
        'price',
        'gst_percent'
    )

    search_fields = ('product_name',)


# ================= PRODUCT =================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'gst_percent', 'company')
    search_fields = ('name',)
    list_filter = ('company',)


# ================= PRODUCT CATEGORY =================
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company')
    search_fields = ('name',)