import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, F, Q, DecimalField, Value
from django.db.models.functions import TruncDate, TruncHour, Coalesce
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Order, OrderItem, Product, ProductVariant, Category,
    KOT, Table, Customer, OrderPayment, Expense, Employee, RefundNote
)

def get_date_range(request):
    """Helper to parse start_date and end_date from query params."""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = timezone.now().date() - timedelta(days=30)
            end_date = timezone.now().date()
    else:
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
    return start_date, end_date

# =========================================================
# 1. Comprehensive Sales & Revenue Analytics
# =========================================================
@swagger_auto_schema(method='get', operation_summary="1. Comprehensive Sales & Revenue Analytics")
@api_view(['GET'])
@permission_classes([AllowAny])
def comprehensive_sales_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    orders = Order.objects.filter(
        outlet_id=outlet_id,
        order_date__date__gte=start_date,
        order_date__date__lte=end_date,
        status__in=['completed', 'settled']
    )
    
    # 1. Overview Stats
    total_revenue = orders.aggregate(t=Sum('total_price'))['t'] or Decimal('0.00')
    total_tax = orders.aggregate(t=Sum('gst'))['t'] or Decimal('0.00')
    total_orders = orders.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0.00')
    
    # 2. Graphs
    # Daily Trend
    daily_sales = (
        orders.annotate(date=TruncDate('order_date'))
        .values('date')
        .annotate(total=Sum('total_price'), count=Count('id'))
        .order_by('date')
    )
    daily_trend = [{"date": str(item['date']), "revenue": float(item['total'] or 0), "orders": item['count']} for item in daily_sales]
    
    # Order Type Split (Dine-in vs Takeaway)
    dine_in_orders = orders.filter(table_number__isnull=False).aggregate(t=Sum('total_price'))['t'] or 0
    takeaway_orders = orders.filter(table_number__isnull=True).aggregate(t=Sum('total_price'))['t'] or 0
    order_type_split = [
        {"name": "Dine-in", "value": float(dine_in_orders)},
        {"name": "Takeaway", "value": float(takeaway_orders)}
    ]
    
    # 3. Table Data
    table_data = []
    for o in orders.order_by('-order_date')[:100]: # limit 100 for table
        table_data.append({
            "order_number": o.order_number,
            "date": o.order_date.strftime("%Y-%m-%d %H:%M"),
            "type": "Dine-in" if o.table_number else "Takeaway",
            "total_price": float(o.total_price),
            "gst": float(o.gst),
            "payment_mode": o.mode
        })
        
    return Response({
        "overview_stats": {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "avg_order_value": float(avg_order_value),
            "total_gst": float(total_tax)
        },
        "graphs": {
            "daily_trend": daily_trend,
            "order_type_split": order_type_split
        },
        "table_data": table_data
    })


# =========================================================
# 2. Menu & Product Performance Analytics
# =========================================================
@swagger_auto_schema(method='get', operation_summary="2. Menu & Product Performance Analytics")
@api_view(['GET'])
@permission_classes([AllowAny])
def menu_performance_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    order_items = OrderItem.objects.filter(
        order__outlet_id=outlet_id,
        order__order_date__date__gte=start_date,
        order__order_date__date__lte=end_date,
        order__status__in=['completed', 'settled']
    )
    
    # Overview
    total_items_sold = order_items.aggregate(t=Sum('quantity'))['t'] or 0
    total_revenue = order_items.aggregate(t=Sum('total_price'))['t'] or 0
    
    # Graphs - Top 10 Products
    product_sales = (
        order_items.filter(product__isnull=False)
        .values('product__name', 'product__category__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('total_price'))
        .order_by('-qty')
    )
    
    variant_sales = (
        order_items.filter(product_variant__isnull=False)
        .values('product_variant__name', 'product_variant__product__category__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('total_price'))
        .order_by('-qty')
    )
    
    # Merge and sort
    merged_sales = []
    for p in product_sales:
        merged_sales.append({
            "name": p['product__name'],
            "category": p['product__category__name'] or "Uncategorized",
            "qty": p['qty'],
            "revenue": float(p['revenue'] or 0)
        })
    for v in variant_sales:
        merged_sales.append({
            "name": v['product_variant__name'],
            "category": v['product_variant__product__category__name'] or "Uncategorized",
            "qty": v['qty'],
            "revenue": float(v['revenue'] or 0)
        })
        
    merged_sales.sort(key=lambda x: x['qty'], reverse=True)
    
    top_10 = merged_sales[:10]
    
    if merged_sales:
        top_selling = merged_sales[0]['name']
        lowest_selling = merged_sales[-1]['name']
    else:
        top_selling = "N/A"
        lowest_selling = "N/A"
        
    # Revenue by Category
    category_revenue = {}
    for item in merged_sales:
        cat = item['category']
        category_revenue[cat] = category_revenue.get(cat, 0) + item['revenue']
        
    cat_graph = [{"name": k, "value": v} for k, v in category_revenue.items()]
    
    return Response({
        "overview_stats": {
            "total_items_sold": total_items_sold,
            "total_product_revenue": float(total_revenue),
            "top_selling_item": top_selling,
            "lowest_selling_item": lowest_selling
        },
        "graphs": {
            "top_10_products": top_10,
            "revenue_by_category": cat_graph
        },
        "table_data": merged_sales
    })


# =========================================================
# 3. Kitchen Efficiency & KOT Analytics
# =========================================================
@swagger_auto_schema(method='get', operation_summary="3. Kitchen Efficiency & KOT Analytics")
@api_view(['GET'])
@permission_classes([AllowAny])
def kitchen_efficiency_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    kots = KOT.objects.filter(
        table__outlet_id=outlet_id,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    total_kots = kots.count()
    
    # We don't have KOT completion time out of the box in the model (KOT has created_at only)
    # I will simulate or use Order items 'ready_to_serve' status if applicable, or just show volume.
    
    kot_volume = (
        kots.annotate(hour=TruncHour('created_at'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    
    heatmap = [{"time": item['hour'].strftime("%Y-%m-%d %H:%M"), "kots": item['count']} for item in kot_volume]
    
    table_data = []
    for k in kots.order_by('-created_at')[:100]:
        table_data.append({
            "kot_number": k.kot_number,
            "table_number": k.table.table_number if k.table else "N/A",
            "order_number": k.order.order_number if k.order else "N/A",
            "created_at": k.created_at.strftime("%Y-%m-%d %H:%M"),
            "items_count": len(k.items) if isinstance(k.items, list) else 0
        })

    return Response({
        "overview_stats": {
            "total_kots": total_kots,
            "avg_prep_time_mins": "Not Tracked", # Requires KOT completed_at timestamp
            "peak_kitchen_hour": heatmap[0]['time'] if heatmap else "N/A"
        },
        "graphs": {
            "kot_hourly_volume": heatmap
        },
        "table_data": table_data
    })


# =========================================================
# 4. Table & Dine-in Utilization Report
# =========================================================
@swagger_auto_schema(method='get', operation_summary="4. Table & Dine-in Utilization Report")
@api_view(['GET'])
@permission_classes([AllowAny])
def table_utilization_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    orders = Order.objects.filter(
        outlet_id=outlet_id,
        table_number__isnull=False,
        order_date__date__gte=start_date,
        order_date__date__lte=end_date,
        status__in=['completed', 'settled']
    )
    
    total_orders = orders.count()
    total_rev = orders.aggregate(t=Sum('total_price'))['t'] or 0
    avg_order = total_rev / total_orders if total_orders > 0 else 0
    
    table_metrics = (
        orders.values('table_number__table_number')
        .annotate(revenue=Sum('total_price'), count=Count('id'))
        .order_by('-revenue')
    )
    
    table_data = []
    for t in table_metrics:
        table_data.append({
            "table_no": t['table_number__table_number'],
            "total_orders": t['count'],
            "total_revenue": float(t['revenue'] or 0)
        })
        
    most_profitable = table_data[0]['table_no'] if table_data else "N/A"
    
    return Response({
        "overview_stats": {
            "total_dine_in_orders": total_orders,
            "most_profitable_table": most_profitable,
            "avg_dine_in_order_value": float(avg_order),
            "total_dine_in_revenue": float(total_rev)
        },
        "graphs": {
            "revenue_by_table": table_data
        },
        "table_data": table_data
    })


# =========================================================
# 5. Customer Retention & Loyalty Report
# =========================================================
@swagger_auto_schema(method='get', operation_summary="5. Customer Retention & Loyalty Report")
@api_view(['GET'])
@permission_classes([AllowAny])
def customer_retention_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    customers = Customer.objects.filter(
        order__outlet_id=outlet_id,
        order__order_date__date__gte=start_date,
        order__order_date__date__lte=end_date
    ).distinct()
    
    total_customers = customers.count()
    
    # Calculate repeats (Customers with > 1 order overall)
    # This is a heavy query if we count globally, so let's do it for the period
    customer_stats = (
        Order.objects.filter(
            outlet_id=outlet_id,
            customer__isnull=False,
            status__in=['completed', 'settled']
        )
        .values('customer__name', 'customer__phone_number')
        .annotate(visits=Count('id'), spend=Sum('total_price'), last_visit=Max('order_date'))
        .order_by('-spend')
    )
    
    repeats = 0
    new = 0
    total_spend = 0
    table_data = []
    
    for c in customer_stats:
        if c['visits'] > 1:
            repeats += 1
        else:
            new += 1
        total_spend += float(c['spend'] or 0)
            
        table_data.append({
            "name": c['customer__name'],
            "phone": c['customer__phone_number'],
            "total_visits": c['visits'],
            "total_spend": float(c['spend'] or 0),
            "last_visit": c['last_visit'].strftime("%Y-%m-%d") if c['last_visit'] else "N/A"
        })
        
    avg_clv = total_spend / total_customers if total_customers > 0 else 0
    repeat_pct = (repeats / total_customers * 100) if total_customers > 0 else 0
    
    return Response({
        "overview_stats": {
            "total_unique_customers": total_customers,
            "repeat_customers_pct": float(round(repeat_pct, 2)),
            "new_customers": new,
            "avg_customer_lifetime_value": float(round(avg_clv, 2))
        },
        "graphs": {
            "new_vs_repeat": [
                {"name": "New", "value": new},
                {"name": "Repeat", "value": repeats}
            ]
        },
        "table_data": table_data
    })


from django.db.models import Max # Missed import above

# =========================================================
# 6. Payment & Cash Flow Analytics
# =========================================================
@swagger_auto_schema(method='get', operation_summary="6. Payment & Cash Flow Analytics")
@api_view(['GET'])
@permission_classes([AllowAny])
def payment_analytics_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    payments = OrderPayment.objects.filter(
        order__outlet_id=outlet_id,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    total_collected = payments.aggregate(t=Sum('amount'))['t'] or 0
    
    refunds = RefundNote.objects.filter(
        order__outlet_id=outlet_id,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).aggregate(t=Sum('refund_amount'))['t'] or 0
    
    mode_split = (
        payments.values('payment_mode')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    
    graph_data = [{"name": m['payment_mode'], "value": float(m['total'] or 0)} for m in mode_split]
    
    table_data = []
    for p in payments.order_by('-created_at')[:100]:
        table_data.append({
            "date": p.created_at.strftime("%Y-%m-%d %H:%M"),
            "order_number": p.order.order_number,
            "amount": float(p.amount),
            "mode": p.payment_mode,
            "transaction_id": p.transaction_id or "N/A"
        })
        
    return Response({
        "overview_stats": {
            "total_collected": float(total_collected),
            "total_refunded": float(refunds),
            "net_cash_flow": float(total_collected - refunds)
        },
        "graphs": {
            "revenue_by_mode": graph_data
        },
        "table_data": table_data
    })


# =========================================================
# 7. Expense & Profitability Report
# =========================================================
@swagger_auto_schema(method='get', operation_summary="7. Expense & Profitability Report")
@api_view(['GET'])
@permission_classes([AllowAny])
def expense_profitability_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    expenses = Expense.objects.filter(
        outlet_id=outlet_id,
        expense_date__date__gte=start_date,
        expense_date__date__lte=end_date
    )
    
    total_expense = expenses.aggregate(t=Sum('amount'))['t'] or 0
    
    orders = Order.objects.filter(
        outlet_id=outlet_id,
        order_date__date__gte=start_date,
        order_date__date__lte=end_date,
        status__in=['completed', 'settled']
    )
    total_revenue = orders.aggregate(t=Sum('total_price'))['t'] or 0
    
    net_profit = total_revenue - total_expense
    
    exp_graph = (
        expenses.annotate(date=TruncDate('expense_date'))
        .values('date')
        .annotate(total=Sum('amount'))
        .order_by('date')
    )
    
    daily_expenses = [{"date": str(e['date']), "expense": float(e['total'] or 0)} for e in exp_graph]
    
    table_data = []
    for e in expenses.order_by('-expense_date')[:100]:
        table_data.append({
            "date": e.expense_date.strftime("%Y-%m-%d %H:%M"),
            "title": e.title,
            "amount": float(e.amount)
        })
        
    return Response({
        "overview_stats": {
            "total_revenue": float(total_revenue),
            "total_expenses": float(total_expense),
            "net_profit": float(net_profit)
        },
        "graphs": {
            "daily_expenses": daily_expenses
        },
        "table_data": table_data
    })


# =========================================================
# 8. Staff & Shift Performance Report
# =========================================================
@swagger_auto_schema(method='get', operation_summary="8. Staff & Shift Performance Report")
@api_view(['GET'])
@permission_classes([AllowAny])
def staff_performance_report(request, outlet_id):
    # Depending on how orders are tracked to staff. 
    # Usually Order model has an `employee` or `taken_by` field.
    # We will simulate this or use employee data if available.
    return Response({
        "overview_stats": {
            "top_performer": "Not Tracked",
            "avg_orders_per_staff": 0
        },
        "graphs": {
            "orders_by_staff": []
        },
        "table_data": []
    })


# =========================================================
# 9. Inventory & Stockout Impact Analytics
# =========================================================
@swagger_auto_schema(method='get', operation_summary="9. Inventory & Stockout Impact Analytics")
@api_view(['GET'])
@permission_classes([AllowAny])
def inventory_stockout_report(request, outlet_id):
    # Basic stockout tracking
    stockouts = Product.objects.filter(
        outlet_id=outlet_id,
        is_stock_out=True
    )
    
    table_data = []
    for p in stockouts:
        table_data.append({
            "product_name": p.name,
            "price": float(p.price)
        })
        
    return Response({
        "overview_stats": {
            "active_stockouts": stockouts.count(),
            "est_revenue_lost": 0 # requires historic daily average calculation
        },
        "graphs": {
            "stockouts": []
        },
        "table_data": table_data
    })


# =========================================================
# 10. Discount & Coupon Impact Analytics
# =========================================================
@swagger_auto_schema(method='get', operation_summary="10. Discount & Coupon Impact Analytics")
@api_view(['GET'])
@permission_classes([AllowAny])
def discount_impact_report(request, outlet_id):
    start_date, end_date = get_date_range(request)
    
    # We don't have a distinct "discount_amount" on Order model out of the box in the snippet,
    # but payment_mode = 'coupon' is tracked. We will track coupon usage.
    coupon_payments = OrderPayment.objects.filter(
        order__outlet_id=outlet_id,
        payment_mode='coupon',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    total_coupons = coupon_payments.count()
    total_discount = coupon_payments.aggregate(t=Sum('amount'))['t'] or 0
    
    table_data = []
    for c in coupon_payments.order_by('-created_at')[:100]:
        table_data.append({
            "order_number": c.order.order_number,
            "coupon_discount": float(c.amount),
            "date": c.created_at.strftime("%Y-%m-%d %H:%M")
        })
        
    return Response({
        "overview_stats": {
            "total_coupon_uses": total_coupons,
            "total_discount_given": float(total_discount)
        },
        "graphs": {
            "coupon_trend": []
        },
        "table_data": table_data
    })
