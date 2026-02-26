# -*- coding: utf-8 -*-
###############################################################################
#  ResortPro 19 - Hotel Management System
#  Migrated from Cybrosys Hotel Management v18 → Odoo 19 Community
#  Migration target: Odoo 19.0 + Python 3.12
###############################################################################
{
    'name': 'ResortPro 19 - Hotel Management',
    'version': '19.0.1.0.0',
    'category': 'Industries',
    'summary': 'Complete Hotel Management System for Resort (30 Rooms) - Odoo 19 Community',
    'description': """
        ResortPro 19 - Nâng cấp từ Cybrosys Hotel Management v18.
        Quản lý phòng, đặt phòng, ăn uống, sự kiện, xe và night audit.
        Tương thích Odoo 19 Community + Python 3.12.
    """,
    'author': 'ResortPro Migration',
    'website': '',
    'depends': ['account', 'event', 'fleet', 'lunch', 'stock'],
    'data': [
        'security/hotel_management_odoo_groups.xml',
        'security/hotel_management_odoo_security.xml',
        'security/ir.model.access.csv',
        'data/ir_data_sequence.xml',
        'data/ir_cron_data.xml',
        'views/account_move_views.xml',
        'views/hotel_menu_views.xml',
        'views/hotel_amenity_views.xml',
        'views/hotel_service_views.xml',
        'views/hotel_floor_views.xml',
        'views/lunch_product_views.xml',
        'views/fleet_vehicle_model_views.xml',
        'views/room_booking_views.xml',
        'views/maintenance_team_views.xml',
        'views/maintenance_request_views.xml',
        'views/cleaning_team_views.xml',
        'views/cleaning_request_views.xml',
        'views/food_booking_line_views.xml',
        'views/dashboard_view.xml',
        'wizard/room_booking_detail_views.xml',
        'wizard/sale_order_detail_views.xml',
        'views/reporting_views.xml',
        'views/night_audit_views.xml',
        'report/room_booking_reports.xml',
        'report/sale_order_reports.xml',
        'views/product_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hotel_management_odoo/static/src/js/action_manager.js',
            'hotel_management_odoo/static/src/css/dashboard.css',
            'hotel_management_odoo/static/src/js/dashboard_action.js',
            'hotel_management_odoo/static/src/xml/dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
