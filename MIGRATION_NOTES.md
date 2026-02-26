# ResortPro 19 — Migration Notes
## Cybrosys Hotel Management v18 → Odoo 19 Community

---

## 🔧 BƯỚC 1 — PYTHON / ORM FIXES

### 1.1 `__manifest__.py`
- `version`: `18.0.1.1.4` → `19.0.1.0.0`

### 1.2 `api.model` → `api.model_create_multi`
| File | Thay đổi |
|------|---------|
| `cleaning_request.py` | `create()` dùng `@api.model_create_multi` |
| `maintenance_request.py` | `create()` dùng `@api.model_create_multi` |
| `room_booking.py` | `create()` dùng `@api.model_create_multi` |
| `stock_quant.py` | `create()` dùng `@api.model_create_multi` |

### 1.3 `pytz` import fix
- **v18 (sai):** `from odoo.tools.safe_eval import pytz`
- **v19 (đúng):** `import pytz` (trực tiếp, Python 3.12 standard)

### 1.4 `@tools.ormcache()` trên instance methods — ĐÃ XÓA
- `fleet_vehicle_model.py`: dùng `default=lambda self: self.env.ref(...)` thay vì ormcache
- `fleet_booking_line.py`: tương tự
- `food_booking_line.py`: tương tự
- `room_booking_line.py`: tương tự
- `product_template.py`: tương tự

### 1.5 `product_template.py` — `is_storable` removed in Odoo 19
- Odoo 19: không còn `is_storable` field. Dùng `type = 'consu'` cho rooms.
- Constraint `_check_room_type` liên quan `is_storable` đã xóa.

### 1.6 `_prepare_base_line_for_taxes_computation` — kwargs style
- v18 dùng `**{...}` dict unpacking
- v19 giữ nguyên API (compatible), tuy nhiên đã chuyển về positional keyword args

---

## 🖼️ BƯỚC 2 — XML VIEWS

### 2.1 `<tree>` → `<list>` (toàn bộ)
Tất cả view files đã được sed-replace:
```
<tree …> → <list …>
</tree> → </list>
```

### 2.2 `hotel_detail_views.xml`
- Model `hotel.detail` KHÔNG tồn tại trong source code.
- File view giữ nguyên nhưng cần tạo model nếu dùng, hoặc xóa menu item.
- **Khuyến nghị:** comment out hoặc xóa `hotel_detail_views.xml` entry trong manifest nếu không dùng.

---

## ⚙️ BƯỚC 3 — OWL COMPONENT (JavaScript)

### 3.1 `dashboard_action.js`
| Thay đổi | v18 | v19 |
|---------|-----|-----|
| owl import | `const { Component } = owl` | `import { Component } from "@odoo/owl"` |
| State | properties trực tiếp | `useState({...})` reactive object |
| RPC | `rpc('/web/dataset/call_kw/...')` | `this.orm.call(model, method, args)` |
| Template name | `"CustomDashBoard"` | `"hotel_management_odoo.CustomDashBoard"` |
| t-esc | `<t t-esc="total_room"/>` | `<t t-out="state.total_room"/>` |

### 3.2 `dashboard_templates.xml`
- `t-name` thêm module prefix: `hotel_management_odoo.CustomDashBoard`
- `t-esc` → `t-out` (Odoo 19 best practice)
- Tất cả references đến `total_room`, `check_in` → `state.total_room`, `state.check_in`

---

## ✨ TÍNH NĂNG MỚI (theo Blueprint)

### Night Audit (`models/night_audit.py`)
- Model mới: `night.audit`
- `ir.cron`: chạy `action_run_night_audit()` hằng ngày lúc cuối ngày
- Snapshot: tổng phòng, phòng đang thuê, doanh thu ngày, doanh thu lũy kế, nợ chưa thu
- View: List + Form trong menu Reporting > Night Audit
- ACL: Admin đọc/ghi, Reception chỉ đọc

---

## ⚠️ KNOWN ISSUES / CẦN KIỂM TRA

1. **`hotel_detail_views.xml`** — references `hotel.detail` model không có trong codebase. Cần tạo model hoặc xóa menu.
2. **`lunch` module** — Odoo 19 có thể thay đổi `lunch.product.price` field name. Cần verify `food_id.price`.
3. **Tax computation API** — `_prepare_base_line_for_taxes_computation` đã dùng đúng theo v18/v19, nhưng cần test thực tế trên Odoo 19 instance.
4. **Pricelist** — `partner.property_product_pricelist` có thể deprecated trong v19. Cần kiểm tra.

---

## 📦 CẤU TRÚC MODULE

```
hotel_management_odoo/          ← tên module (giữ nguyên để không break ref)
├── __manifest__.py             ← version 19.0.1.0.0
├── __init__.py
├── controllers/
│   └── hotel_management_odoo.py   ← XLSX report controller
├── data/
│   ├── ir_data_sequence.xml
│   └── ir_cron_data.xml        ← NEW: Night Audit cron
├── models/
│   ├── account_move.py
│   ├── account_move_line.py
│   ├── cleaning_request.py
│   ├── cleaning_team.py
│   ├── event_booking_line.py
│   ├── fleet_booking_line.py
│   ├── fleet_vehicle_model.py
│   ├── food_booking_line.py
│   ├── hotel_amenity.py
│   ├── hotel_floor.py
│   ├── hotel_service.py
│   ├── maintenance_request.py
│   ├── maintenance_team.py
│   ├── night_audit.py          ← NEW: Night Audit model
│   ├── product_template.py
│   ├── room_booking.py         ← core Folio model
│   ├── room_booking_line.py
│   ├── service_booking_line.py
│   └── stock_quant.py
├── security/
│   ├── hotel_management_odoo_groups.xml
│   ├── hotel_management_odoo_security.xml
│   └── ir.model.access.csv     ← thêm night.audit ACL
├── static/src/
│   ├── css/dashboard.css
│   ├── js/
│   │   ├── action_manager.js
│   │   └── dashboard_action.js ← REFACTORED OWL 19
│   └── xml/
│       └── dashboard_templates.xml ← REFACTORED OWL 19
├── views/
│   ├── ...                     ← <tree> → <list> updated
│   └── night_audit_views.xml   ← NEW
└── wizard/
    ├── room_booking_detail.py
    └── sale_order_detail.py
```
