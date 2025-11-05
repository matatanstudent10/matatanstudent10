# Payment Receipt Portal Module

Portal management system for supplier payment receipt processing in Odoo 15.

## Overview

This module enables a scalable portal-based workflow for managing supplier payment receipts. Portal users (suppliers or designated personnel) can:

- View assigned payment receipt tasks
- Upload evidence documents (receipts, proof of delivery, invoices, etc.)
- Mark tasks as completed
- Track task deadlines and status

## Key Features

### 1. **Portal User Interface**
- Task dashboard with kanban-style cards
- Real-time deadline tracking
- File upload with drag-and-drop support
- Task status indicators (Draft, In Progress, Completed, Overdue)

### 2. **Backend Management**
- Create and assign payment tasks to portal users
- Monitor task progress and file uploads
- Workflow audit trail
- Security groups and access controls

### 3. **Automated Notifications**
- Email notifications for task assignment
- Status update emails (started, completed)
- Supplier confirmation emails
- Manager review notifications
- Overdue reminders

### 4. **File Management**
- Automatic file validation (type and size)
- Support for multiple file formats (PDF, Images, Office docs)
- File descriptions and categorization
- Attachment history

### 5. **Audit Trail**
- Complete workflow history
- User action logging
- State change tracking
- Timestamps for all activities

## Installation

### Prerequisites
- Odoo 15.0+
- Modules: `base`, `stock`, `mail`, `portal`

### Steps

1. Copy module to `/odoo15/custom/addons/delivery_expenses/`
2. Update module list:
   ```bash
   python3 /odoo15/odoo-server/odoo-bin \
     -c /etc/odoo15-1-server.conf \
     -d environmentodoo \
     --stop-after-init \
     --update=all
   ```
3. Install module:
   ```bash
   python3 /odoo15/odoo-server/odoo-bin \
     -c /etc/odoo15-1-server.conf \
     -d environmentodoo \
     -i delivery_expenses \
     --stop-after-init
   ```

## Usage

### For Administrators/Managers

1. Navigate to **Payment Receipts** menu
2. Go to **Payment Tasks**
3. Create new payment task:
   - Select payment receipt
   - Assign to portal user
   - Set deadline
4. Monitor progress through task list
5. Review uploaded files and audit logs

### For Portal Users

1. Login to portal
2. Navigate to **My Payment Receipt Tasks** section
3. View assigned tasks with deadlines
4. Click on task to view details
5. Upload required evidence documents
6. Mark task as completed

### Workflow States

```
DRAFT
  ↓
IN_PROGRESS (User starts working)
  ↓
COMPLETED (With files uploaded)

Or → CANCELLED (at any point)
```

### File Types

Supported file categorization:
- **Receipt**: Original payment receipt
- **Proof of Delivery**: Evidence of delivery/execution
- **Invoice**: Supporting invoice document
- **Other Document**: Additional evidence

## Security

### Security Groups

1. **Payment Receipt User** (read-only access to assigned tasks)
   - Can view assigned tasks
   - Can upload files
   - Can mark tasks as completed
   - Cannot modify/delete tasks

2. **Payment Receipt Manager** (full access)
   - Can create and assign tasks
   - Can view all tasks
   - Can modify task details
   - Can review files
   - Cannot delete tasks (audit trail protection)

### Record Rules

- Portal users can only see tasks assigned to them
- Managers can see all tasks
- File uploads limited to task owner
- Audit logs are read-only

## Models

### `delivery_expenses.payment_task`
Main task model for payment receipt processing.

**Key Fields:**
- `payment_receipt_id`: Many2one → `supplier.payment.receipt`
- `assigned_user_id`: Many2one → `res.partner` (portal user)
- `state`: Selection (draft, in_progress, completed, cancelled)
- `deadline`: Date field for task deadline
- `receipt_file_ids`: One2many → payment receipt files
- `workflow_log_ids`: One2many → workflow audit logs

**Computed Fields:**
- `files_count`: Number of uploaded files
- `days_remaining`: Days until deadline
- `is_overdue`: Boolean indicating if task is overdue
- `supplier_id`, `receipt_amount`, `receipt_date`: Related to receipt

**Methods:**
- `action_assign()`: Assign task to user
- `action_start_progress()`: Mark as in progress
- `action_mark_completed()`: Mark as completed (requires files)
- `action_cancel()`: Cancel task

### `delivery_expenses.payment_receipt_file`
File/attachment model for evidence documents.

**Key Fields:**
- `payment_task_id`: Many2one → payment task
- `attachment_id`: Many2one → `ir.attachment`
- `file_type`: Selection (receipt, proof_of_delivery, invoice, other)
- `uploaded_by`: Many2one → `res.partner`
- `upload_date`: Datetime (readonly)
- `is_valid`: Boolean (auto-validated)
- `validation_notes`: Validation messages

**Validations:**
- Allowed MIME types: PDF, JPEG, PNG, DOCX, DOC, XLSX, XLS
- Max file size: 10 MB
- Auto-validation on file creation

### `delivery_expenses.payment_receipt_workflow_log`
Audit trail model for workflow actions.

**Key Fields:**
- `payment_task_id`: Many2one → payment task
- `action`: Selection of actions (create, assign, start, complete, cancel, email)
- `user_id`: Many2one → `res.users` (who performed action)
- `timestamp`: Datetime (immutable)
- `change_data`: JSON data of changes
- `notes`: Optional notes about action

**Read-only:** All fields are immutable after creation

## Email Templates

Module includes 5 email templates:

1. **Payment Task Assigned** - Notifies user of new task assignment
2. **Payment Task Started** - Confirms user has started working
3. **Payment Task Completed (Supplier)** - Notifies supplier of verification
4. **Payment Task Completed (Manager)** - Notifies manager of completion
5. **Payment Task Overdue Reminder** - Reminds user of overdue task

## Views

### Backend Views

**Tree View**: Quick overview of all tasks
- Default sorting by deadline
- Color coding: green (completed), red (overdue), gray (cancelled), orange (in progress)
- Inline action buttons

**Form View**: Detailed task information
- Task assignment and deadline
- Receipt details (readonly)
- File upload history
- Workflow audit trail
- Chatter for notes/discussion

**Kanban View**: Visual task management
- Group by status
- Color-coded cards
- Quick filters for state

**Search View**: Advanced filtering
- Filter by status, user, supplier, deadline
- Group by state, user, supplier, deadline
- Saved filters for quick access

### Portal Views

**Task List**: Dashboard of assigned tasks
- Kanban-style cards
- Status badges with colors
- File count indicator
- Pagination support
- Filtering and sorting

**Task Detail**: Full task information
- Receipt and supplier details
- Deadline with countdown
- File upload area (drag-and-drop)
- Uploaded files list with download
- Action buttons
- Chatter/comments section

## Scalability Considerations

### Database Performance
- Indexed fields: `deadline`, `state`, `assigned_user_id`, `timestamp`
- Computed fields use `store=True` for frequently accessed data
- SQL constraint for unique receipt-user assignment

### Portal Performance
- Pagination (10 tasks per page)
- Minimal template rendering
- File size limits to prevent storage issues
- Async email sending with queue jobs (future enhancement)

### Multi-Company Support
- All tasks include `company_id` field
- Security rules respect company boundaries
- Isolate data per company in reports

### Future Enhancements
- Async file processing with Celery
- Batch email notifications with queue jobs
- Payment receipt API integration
- Mobile app support
- Advanced analytics/reporting
- Webhook notifications
- 2FA for sensitive operations

## Troubleshooting

### Files not uploading
- Check file size (max 10MB)
- Verify MIME type is supported
- Ensure user has upload permissions
- Check server disk space

### Emails not sending
- Verify SMTP configuration in Odoo settings
- Check `ir.mail.server` configuration
- Review Odoo logs for email errors
- Ensure recipient emails are valid

### Portal access issues
- Verify user is linked to a partner
- Check security group assignment
- Confirm user isn't in inactive state
- Check record rules in Settings > Database

### Task visibility issues
- Confirm user is assigned as `assigned_user_id`
- Check if record rules are active
- Verify user is in correct security group

## Development Notes

### File Validation
Files are validated in `PaymentReceiptFile._validate_file()`:
- MIME type whitelist
- File size limit (10MB)
- Auto-flagged on creation if invalid

### Workflow Logging
Every action creates a `PaymentReceiptWorkflowLog` entry:
- Automatic through `_log_workflow(action)` method
- Immutable record for audit trail
- Includes user, timestamp, and optional notes

### Email Notification Flow
1. Action is performed (assign, start, complete)
2. Method calls `_notify_*()` with template ID
3. Template is rendered with record context
4. Email is sent via `ir.mail.server`
5. Action is logged to workflow history

### Portal Controller Security
- All routes check `assigned_user_id == current_user.partner_id`
- File operations validate task ownership
- CSRF protection on all POST routes
- Graceful error handling with redirects

## Configuration

### Settings
Currently no configuration settings. Recommended future additions:
- Allowed file types
- Max file size
- Email notification delay
- Task auto-assignment rules
- Overdue reminder intervals

### Permissions
Assign users to security groups:
1. Go to Settings → Users & Companies → Users
2. Select user
3. Add to "Payment Receipt User" or "Payment Receipt Manager"

### Email Configuration
1. Go to Settings → Technical → Email
2. Configure SMTP server (`ir.mail.server`)
3. Set sender email for notifications

## License

LGPL-3

## Support

For issues or feature requests, contact the development team.

---

**Module Version:** 15.0.1.0.0
**Author:** Empaquetaduras y Empaques S.A.
**Maintained:** 2024
