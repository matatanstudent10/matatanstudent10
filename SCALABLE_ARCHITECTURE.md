# Delivery Expenses - Scalable Architecture Guide

## Current Module Purpose

**Version 1.0**: Payment Receipt Portal
- Manages supplier payment receipt tasks
- Portal users upload evidence documents (receipts, proofs of delivery)
- Tracks task completion and deadlines
- Automatic email notifications

---

## Architecture Design for Scalability

This module is designed with a **horizontal extension** pattern. New features can be added without modifying existing code.

### Current Structure

```
delivery_expenses/
├── controllers/
│   ├── __init__.py
│   └── payment_receipt_portal.py          ← Portal access layer
├── models/
│   ├── __init__.py
│   ├── payment_task.py                    ← Task management model
│   └── payment_receipt_file.py            ← File handling model
├── views/
│   ├── views.xml                          ← Backend views
│   ├── email_templates.xml                ← Notifications
│   └── portal_templates.xml               ← Portal UI
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
└── demo/
    └── demo.xml                           ← Test data
```

---

## How to Add New Features

### Pattern 1: New Document Type (e.g., Shipment Evidence)

**Example**: Add "shipment evidence" tracking alongside payment receipts

**Steps**:

1. **Create new model** (`models/shipment_evidence.py`):
   ```python
   class ShipmentEvidence(models.Model):
       _name = 'delivery_expenses.shipment_evidence'
       _description = 'Shipment Evidence'
       _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

       # Similar structure to PaymentTask
       task_id = fields.Many2one('delivery_expenses.payment_task')
       evidence_type = fields.Selection(...)
       files_ids = fields.One2many(...)
   ```

2. **Add to models/__init__.py**:
   ```python
   from . import shipment_evidence
   ```

3. **Create views** (`views/shipment_evidence_views.xml`):
   - Backend forms for staff
   - Portal templates for users

4. **Create controller routes** (in `payment_receipt_portal.py`):
   ```python
   @http.route('/my/shipment-evidence/...')
   def portal_shipment_evidence(self, ...):
       # New routes for shipment evidence
   ```

---

### Pattern 2: New Notification Type

**Example**: Add SMS notifications in addition to email

**Steps**:

1. **Create notification module** (or extend existing):
   ```python
   # In payment_task.py
   def _send_notification(self, template_xml_id, notify_channels=['email']):
       """Send notifications via multiple channels"""
       if 'email' in notify_channels:
           self._send_email(template_xml_id)
       if 'sms' in notify_channels:
           self._send_sms(template_xml_id)
   ```

2. **Add SMS templates** to `email_templates.xml`:
   ```xml
   <record id="payment_task_assigned_sms" model="ir.mail.template">
       <!-- SMS template -->
   </record>
   ```

---

### Pattern 3: New Workflow State

**Example**: Add "verification" state for administrative review

**Steps**:

1. **Update model selection field**:
   ```python
   state = fields.Selection([
       ('draft', 'Draft'),
       ('in_progress', 'In Progress'),
       ('verification', 'Awaiting Verification'),  ← NEW
       ('completed', 'Completed'),
       ('cancelled', 'Cancelled')
   ])
   ```

2. **Add transition method**:
   ```python
   def action_submit_for_verification(self):
       self.state = 'verification'
   ```

3. **Update portal templates** to show new state

4. **Add backend views** for verification step

---

### Pattern 4: New Portal Feature (e.g., Batch Upload)

**Example**: Allow users to upload multiple files at once

**Steps**:

1. **Create new controller route**:
   ```python
   @http.route('/my/payment-tasks/<int:task_id>/batch-upload', ...)
   def portal_batch_upload(self, task_id, **kwargs):
       # Handle batch file upload
   ```

2. **Add template for batch UI**:
   ```xml
   <template id="portal_batch_upload_form">
       <!-- Drag-and-drop upload UI -->
   </template>
   ```

3. **Extend PaymentReceiptFile model** if needed:
   ```python
   batch_id = fields.Many2one('delivery_expenses.batch_upload')
   ```

---

## Extension Points

### 1. Models
- **Add new models** without modifying existing ones
- Inherit from `mail.thread`, `portal.mixin` for consistency
- Use `related` fields for computed data

### 2. Controllers
- Add new routes in `payment_receipt_portal.py` without modifying existing ones
- Follow naming convention: `portal_<feature_name>_<action>`
- Extend `CustomerPortal` for consistency

### 3. Views
- Add new XML files in `views/` directory
- Use `inherit_id` to extend existing views without modifying them
- Organize by feature: `shipment_evidence_views.xml`, etc.

### 4. Security
- Add new groups for new features
- Extend `ir.model.access.csv` with new access rules
- Create new `security.xml` rules if needed

### 5. Templates
- Add new email templates for new features
- Use consistent naming: `<feature>_<action>_email_template`

---

## Design Principles

### 1. Single Responsibility
- Each model file handles one entity
- Each controller file handles related routes
- Each view file handles related views

### 2. Backward Compatibility
- Never modify existing fields (add new ones)
- Never remove existing states (add new ones)
- Never delete existing routes (add new ones)

### 3. Inheritance over Modification
- Use XPath to extend views
- Use related/computed fields for calculations
- Use inheritance for model extensions

### 4. Portal-First Approach
- All models inherit `portal.mixin`
- All features accessible via portal
- Portal templates match backend workflows

---

## Future Enhancement Ideas

### v1.1: Approval Workflow
- Add manager approval step
- Digital signature integration
- Comment/feedback system

### v1.2: Advanced Reporting
- Task completion analytics
- Overdue task reports
- Supplier performance metrics

### v1.3: Multiple Document Types
- Shipment evidence tracking
- Invoice verification
- Customs documentation

### v1.4: Integration Points
- Webhook notifications
- REST API for external systems
- Mobile app sync

### v2.0: Configurable Workflows
- Custom states per document type
- Conditional transitions
- Dynamic field visibility

---

## Code Style Guidelines

### Naming Conventions

```python
# Models
class PaymentTask(models.Model):
    _name = 'delivery_expenses.payment_task'  # lowercase_underscore

# Methods
def action_mark_completed(self):  # action_* for user actions
def _compute_days_remaining(self):  # _compute_* for computed fields
def _send_email(self, template):  # _private_* for internal methods

# Routes
@http.route('/my/payment-tasks/<int:task_id>/upload')  # /my/<feature>/<action>

# Templates
portal_payment_tasks  # portal_<model_name>
payment_task_form  # <model_name>_<view_type>
```

### Documentation

```python
class PaymentTask(models.Model):
    """
    Short description.

    Longer explanation of:
    - Key features
    - Relationships to other models
    - Important constraints
    """
```

---

## Database Considerations

- Use `related` fields with `store=True` for frequently accessed data
- Avoid computed fields with `store=True` unless performance critical
- Keep `sql_constraints` for unique data integrity
- Index frequently searched fields

---

## Testing New Features

1. **Unit Tests**: Test model logic in isolation
2. **Integration Tests**: Test controller routes
3. **Portal Tests**: Test portal user access
4. **Demo Data**: Add demo records for new features

---

## Version History

- **v1.0** (2024-10): Initial release - Payment Receipt Portal
  - PaymentTask model
  - PaymentReceiptFile model
  - Portal controller with 5 routes
  - Email notifications
  - Demo data

---

## Contact & Documentation

For questions about architecture or extending this module:
1. Review this document first
2. Check expense_portal module for similar patterns
3. Follow existing code conventions
