# Netflix Subscription System Documentation

## Overview

The subscription app handles the complete payment flow for the Netflix clone application using Stripe as the payment processor. Users can browse subscription plans, make payments, and receive confirmation of their subscription.

---

## Architecture

### Components

```
subscription/
├── models.py          # Database models for subscription plans
├── views.py           # View handlers for subscription flow
├── stripe_utils.py    # Stripe integration utilities
├── urls.py            # URL routing for subscription endpoints
├── admin.py           # Django admin configuration
└── templates/
    └── subscription/
        ├── plans.html              # Display available plans
        ├── payment_success.html     # Success page after payment
        └── payment_fail.html        # Cancel/failure page
```

---

## Database Models

### SubscriptionPlan

The `SubscriptionPlan` model represents a subscription tier offered to users.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField (100) | Plan name (e.g., "Basic", "Standard", "Premium") |
| `price` | DecimalField | Price in USD (max 8 digits, 2 decimal places) |
| `duration_days` | PositiveIntegerField | How many days the subscription is valid |
| `stripe_price_id` | CharField (200, nullable) | Stripe Price ID for future recurring payments |

**Example:**
```python
plan = SubscriptionPlan.objects.create(
    name="Premium",
    price=19.99,
    duration_days=30,
    stripe_price_id="price_1Abc123xyz"  # Optional, for recurring billing
)
```

---

## Views & Request Flow

### 1. Plans View (`/subscription/`)

**URL:** `path('', views.plans, name='plans')`

**Handler:** `plans(request)`

Displays all available subscription plans to the user.

**What it does:**
- Fetches all `SubscriptionPlan` objects from the database
- Renders the plans template with the list
- Each plan has a clickable card with "Pay Now" button

**Template Context:**
```python
{
    'plans': <QuerySet of SubscriptionPlan objects>
}
```

**Template:** `subscription/plans.html`

---

### 2. Payment Redirect View (`/subscription/pay/<plan_id>/`)

**URL:** `path("pay/<int:plan_id>/", views.payment_redirect, name="pay")`

**Handler:** `payment_redirect(request, plan_id)`

Initiates Stripe checkout session and redirects user to Stripe's payment page.

**What it does:**
1. Retrieves the selected `SubscriptionPlan` by ID
2. Returns 404 if plan doesn't exist using `get_object_or_404()`
3. Creates a Stripe checkout session with `create_checkout_session()`
4. Redirects to the Stripe checkout URL with HTTP 303 redirect

**Flow:**
```
User clicks "Pay Now" 
    ↓
Plans form submits plan_id to /subscription/pay/{plan_id}/
    ↓
View creates Stripe session
    ↓
Redirects to Stripe checkout URL (https://checkout.stripe.com/...)
    ↓
User completes payment on Stripe
    ↓
Redirects to success_url or cancel_url
```

---

### 3. Success View (`/subscription/payment/success/`)

**URL:** `path("payment/success/", views.payment_success, name="payment_success")`

**Handler:** `payment_success(request)`

Displays a confirmation page after successful payment.

**What it does:**
- Shows a success message with checkmark icon
- Provides a link to return to user profiles
- Confirms that the subscription is now active

**Template:** `subscription/payment_success.html`

---

### 4. Cancel View (`/subscription/payment/cancel/`)

**URL:** `path("payment/cancel/", views.payment_cancel, name="payment_cancel")`

**Handler:** `payment_cancel(request)`

Displays a cancellation/failure page if payment doesn't complete.

**What it does:**
- Shows a cancel message with error icon
- Provides a link to return to plans page to try again
- Explains that payment was unsuccessful

**Template:** `subscription/payment_fail.html`

---

## Stripe Integration

### create_checkout_session() Function

Located in `subscription/stripe_utils.py`, this function creates a Stripe checkout session.

**Signature:**
```python
def create_checkout_session(plan, request=None):
    """
    Creates a Stripe checkout session for the selected plan.
    
    Args:
        plan: SubscriptionPlan object
        request: Django HttpRequest (optional, for building absolute URLs)
    
    Returns:
        Stripe Session object with checkout URL
    """
```

**How it works:**

1. **Import Dependencies:**
   - Imports `reverse` from `django.urls` to generate Django URL names

2. **Build Absolute URLs:**
   - If request is provided, constructs URLs based on request protocol and host
   - Falls back to `http://localhost:8000` for development
   - Ensures URLs work in both development and production environments

3. **URL Generation:**
   ```python
   success_url = base_url + reverse('payment_success')
   # Example: "https://netflix.example.com/subscription/payment/success/"
   
   cancel_url = base_url + reverse('payment_cancel')
   # Example: "https://netflix.example.com/subscription/payment/cancel/"
   ```

4. **Create Stripe Session:**
   - Creates checkout session with Stripe API
   - Specifies payment method: card payments
   - Includes line items with product data and pricing
   - Sets mode to "payment" (one-time payment, not recurring)
   - Attaches success and cancel URLs

**Stripe Configuration:**

Located in `netflix/settings.py`:
```python
STRIPE_PUBLIC_KEY = "pk_test_..."  # Frontend/JavaScript
STRIPE_SECRET_KEY = "sk_test_..."  # Backend (server-side only)
```

⚠️ **Security:** Secret key should never be shared or exposed in frontend code.

**Session Creation Example:**
```python
session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[{
        "price_data": {
            "currency": "usd",
            "unit_amount": 1999,  # $19.99 in cents
            "product_data": {
                "name": "Premium Plan",
            },
        },
        "quantity": 1,
    }],
    mode="payment",
    success_url="https://localhost:8000/subscription/payment/success/",
    cancel_url="https://localhost:8000/subscription/payment/cancel/",
)
# Returns: Stripe Session with .url attribute containing checkout link
```

---

## URL Configuration

**File:** `subscription/urls.py`

```python
urlpatterns = [
    path('', views.plans, name='plans'),
    path("pay/<int:plan_id>/", views.payment_redirect, name="pay"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
]
```

**Included in main project:**
`netflix/urls.py`: `path('subscription/', include('subscription.urls'))`

**Available Routes:**
- `GET /subscription/` → Shows all plans
- `GET /subscription/pay/2/` → Redirects to Stripe for plan ID 2
- `GET /subscription/payment/success/` → Success confirmation
- `GET /subscription/payment/cancel/` → Cancellation page

---

## Templates

### plans.html

**Location:** `subscription/templates/subscription/plans.html`

**Features:**
- Responsive grid layout (1 col mobile, 2 cols tablet, 4 cols desktop)
- Plan cards showing name, duration, and price
- Click to select plan (highlights with red ring)
- Immediate redirect to Stripe checkout
- Dark Netflix-style design

**Key Elements:**
```html
<div class="plan-card" data-plan-id="{{ plan.id }}">
    <div class="bg-blue-800 text-white p-4">
        <h1>{{ plan.name }}</h1>
        <p>{{ plan.duration_days }} days</p>
    </div>
    <div class="mx-4 py-4">
        <p>USD {{ plan.price }}</p>
    </div>
</div>
```

**JavaScript Behavior:**
- Attaches click listeners to plan cards
- Highlights selected plan with red border ("ring-4 ring-red-500")
- Redirects to `/subscription/pay/{plan_id}/`

---

### payment_success.html

**Location:** `subscription/templates/subscription/payment_success.html`

**Features:**
- Green checkmark SVG icon
- "Payment Successful!" message
- Confirmation that account is active
- Link to return to user profiles
- Dark theme with white text

**Content:**
```html
✓ Payment Successful!
Thank you for your subscription. Your account is now active.
[Return to Your Profile button]
```

---

### payment_fail.html

**Location:** `subscription/templates/subscription/payment_fail.html`

**Features:**
- Red X SVG icon
- "Payment Cancelled" message
- Explanation of failure
- Link to return to plans and try again
- Dark theme with white text

**Content:**
```html
✗ Payment Cancelled
Your payment was cancelled. Please try again or choose a different plan.
[Back to Plans button]
```

---

## Complete User Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User visits /subscription/                                  │
│ ✓ View fetches all SubscriptionPlan objects               │
│ ✓ Renders plans.html with plan list                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    User selects plan
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Sends GET request to /subscription/pay/{plan_id}/           │
│ ✓ View gets plan from database                            │
│ ✓ Calls create_checkout_session(plan, request)            │
│ ✓ Builds absolute success/cancel URLs                     │
│ ✓ Creates Stripe session with plan price                  │
│ ✓ Redirects to session.url (Stripe checkout)              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Stripe Checkout Page                                        │
│ (Hosted by Stripe - not our server)                         │
│                                                             │
│ User fills:                                                │
│ • Card number                                              │
│ • Expiry date                                              │
│ • CVC                                                      │
│ • Billing address                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    User submits payment
                          │
          ┌───────────────┴────────────────┐
          │                                │
    Payment Success                 Payment Failed/Cancelled
          │                                │
          ▼                                ▼
    Redirects to               Redirects to
    success_url                 cancel_url
    /subscription/payment/      /subscription/payment/
    success/                     cancel/
          │                                │
          ▼                                ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ Success Page (payment_       │  │ Cancel Page (payment_        │
│ success.html)                │  │ fail.html)                   │
│                              │  │                              │
│ ✓ Green checkmark           │  │ ✗ Red X icon                 │
│ ✓ Success message           │  │ Cancellation message         │
│ ✓ Confirm account active    │  │ Try again option             │
│ [Return to Profile]         │  │ [Back to Plans]              │
└──────────────────────────────┘  └──────────────────────────────┘
```

---

## Admin Interface

**File:** `subscription/admin.py`

The `SubscriptionPlan` model is registered in Django admin:

```python
admin.site.register(SubscriptionPlan)
```

**Admin Features:**
- Create new subscription plans
- Edit existing plans (name, price, duration)
- Delete plans
- View all registered plans
- Filter and search plans

**How to access:**
1. Go to `/admin/`
2. Login with admin credentials
3. Navigate to "Subscription Plans" section
4. Click "Add Plan" to create new subscription tier

---

## Current Subscription Plans

The application comes with 4 pre-created plans:

| ID | Name | Price | Duration |
|-----|------|-------|----------|
| 1 | Basic | $9.99 | 30 days |
| 2 | Standard | $15.99 | 30 days |
| 3 | Premium | $19.99 | 30 days |
| 4 | (Custom) | (varies) | (varies) |

These can be modified in the admin panel.

---

## Configuration

### Required Settings

**File:** `netflix/settings.py`

```python
# Stripe API Keys
STRIPE_PUBLIC_KEY = "pk_test_..."  # For frontend
STRIPE_SECRET_KEY = "sk_test_..."  # For backend

# DEBUG mode
DEBUG = True  # Set to False in production

# Allowed hosts for your domain
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com']
```

### Installed Apps

The subscription app must be registered in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps ...
    'subscription',
]
```

---

## Environment Variables & Security

### Development vs Production

**Development (localhost):**
- Use Stripe test keys
- Success/cancel URLs default to `http://localhost:8000`
- Can test full payment flow with Stripe test cards

**Production:**
- Use Stripe live keys (different from test keys)
- Request object provides actual domain
- URLs generated as `https://your-domain.com/...`
- Enable HTTPS

### Stripe Test Card Numbers

For testing in development:

| Card Type | Number | Exp | CVC |
|-----------|--------|-----|-----|
| Visa | 4242 4242 4242 4242 | 12/25 | 123 |
| Visa (fails) | 4000 0000 0000 0002 | 12/25 | 123 |
| Mastercard | 5555 5555 5555 4444 | 12/25 | 123 |

**Any future expiry date and any 3-digit CVC works in test mode.**

---

## Database Migrations

The subscription app has a migration file:

**File:** `subscription/migrations/0001_initial.py`

This creates the `SubscriptionPlan` table in the database.

**To apply migrations:**
```bash
python manage.py migrate
```

**To create new migrations (after model changes):**
```bash
python manage.py makemigrations subscription
python manage.py migrate
```

---

## Error Handling

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| ImportError: cannot import 'urljoin' | Unused import | Use string concatenation instead |
| 404 on plan selection | Plan ID doesn't exist | Check plan ID exists in database |
| Stripe API error | Invalid/missing API key | Verify STRIPE_SECRET_KEY in settings |
| Redirect fails | Missing reverse URL | Ensure payment_success/cancel views exist |
| Wrong base URL | Request object not passed | Pass request to create_checkout_session |

---

## Future Enhancements

Potential features to add:

1. **Recurring Billing** - Use Stripe subscriptions mode instead of payment
2. **User Subscription Tracking** - Store user's active subscription in database
3. **Subscription Model** - Create UserSubscription model linking users to plans
4. **Webhook Handling** - Process Stripe webhooks for payment confirmations
5. **Subscription Management** - Allow users to upgrade/downgrade/cancel
6. **Email Notifications** - Send confirmation emails after payment
7. **Invoice Generation** - Create PDF invoices for payments
8. **Analytics** - Track subscription sales and metrics

---

## File Organization

```
subscription/
├── __init__.py
├── admin.py                    # Register SubscriptionPlan in admin
├── apps.py
├── models.py                   # SubscriptionPlan model (4 fields)
├── tests.py
├── urls.py                     # 4 URL routes
├── views.py                    # 4 view functions
├── stripe_utils.py             # Stripe session creation
├── migrations/
│   ├── 0001_initial.py        # Create SubscriptionPlan table
│   └── __init__.py
└── templates/
    └── subscription/
        ├── plans.html          # Plan selection UI
        ├── payment_success.html # Success message
        └── payment_fail.html    # Cancel/failure message
```

---

## Testing

### Manual Testing Checklist

- [ ] Visit `/subscription/` and see all plans
- [ ] Click a plan and get redirected to Stripe
- [ ] Complete payment with test card 4242 4242 4242 4242
- [ ] See success page at `/subscription/payment/success/`
- [ ] Click "Return to Profile" link
- [ ] Go back and try with card 4000 0000 0000 0002 (fails)
- [ ] See cancel page at `/subscription/payment/cancel/`
- [ ] Click "Back to Plans" link

### Unit Testing (Future)

```python
# Example test structure
from django.test import TestCase, Client
from .models import SubscriptionPlan

class SubscriptionTestCase(TestCase):
    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan",
            price=9.99,
            duration_days=30
        )
    
    def test_plans_view_loads(self):
        response = self.client.get('/subscription/')
        self.assertEqual(response.status_code, 200)
```

---

## Conclusion

The subscription app provides a complete, user-friendly payment flow using Stripe. It handles:
- ✓ Plan selection
- ✓ Secure payment processing
- ✓ Success/failure handling
- ✓ Admin management of plans

For questions or issues, refer to the [Stripe Documentation](https://stripe.com/docs) or Django documentation.
