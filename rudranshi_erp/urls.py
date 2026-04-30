from django.contrib import admin
from django.urls import path
from core.views import product_list, create_invoice
from core.views import customer_list, create_customer


from core.views import (
    login_page,
    dashboard_page,
    logout_page,
    create_invoice_page,
    view_invoice_page,
    download_invoice_pdf,

    # 🔥 NEW ADD
    pricing,
    subscribe,
    create_product,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # AUTH
    path('', login_page),
    path('dashboard/', dashboard_page),
    path('logout/', logout_page),

    # INVOICE
    path('create-invoice/', create_invoice_page),
    path('invoice/<int:id>/', view_invoice_page),
    path('invoice/<int:id>/pdf/', download_invoice_pdf),

    # 🔥 SUBSCRIPTION SYSTEM
    path('pricing/', pricing),
    path('subscribe/<int:plan_id>/<str:billing_type>/', subscribe),

    path('products/', product_list),
    path('create-product/', create_product),

    path('customers/', customer_list),
    path('create-customer/', create_customer),
]