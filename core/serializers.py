from rest_framework import serializers
from .models import Invoice, InvoiceItem


# 🔹 Invoice Item Serializer
class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['product_name', 'quantity', 'price', 'gst_percent']


# 🔹 Main Invoice Serializer
class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'company',
            'description',
            'items',
            'total_amount',
            'gst_amount',
            'cgst',
            'sgst',
            'igst',
            'is_interstate',
            'final_amount',
            'created_at'
        ]

        read_only_fields = [
            'invoice_number',
            'company',
            'total_amount',
            'gst_amount',
            'cgst',
            'sgst',
            'igst',
            'final_amount',
            'created_at'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        # Invoice create
        invoice = Invoice.objects.create(**validated_data)

        total = 0
        gst_total = 0

        # Items create + calculation
        for item_data in items_data:
            item = InvoiceItem.objects.create(invoice=invoice, **item_data)

            item_total = item.quantity * item.price
            gst = item_total * item.gst_percent / 100

            total += item_total
            gst_total += gst

        # Totals
        invoice.total_amount = total
        invoice.gst_amount = gst_total

        # 🔥 GST SPLIT LOGIC (FIXED INDENTATION)
        if invoice.is_interstate:
            invoice.igst = gst_total
            invoice.cgst = 0
            invoice.sgst = 0
        else:
            invoice.cgst = gst_total / 2
            invoice.sgst = gst_total / 2
            invoice.igst = 0

        invoice.final_amount = total + gst_total

        invoice.save()

        return invoice