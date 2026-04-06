from django.contrib import messages

def process_withdrawal(user, portfolio, transaction):
    """
    Handles withdrawal logic:
    - KYC check
    - Withdraw status check
    - Balance deduction only on success
    """

    # 🔒 KYC check
    if not portfolio.is_kyc_verified:
        return {
            "status": "error",
            "message": "You must complete identity verification (KYC) before making a withdrawal.",
            "redirect": "customer:verify_kyc"
        }

    # 🔍 Withdraw status check (from User model)
    withdraw_status = user.withdraw_status

    # Check if balance is sufficient
    if withdraw_status == "success" and portfolio.cash_balance < transaction.amount:
        return {
            "status": "error",
            "message": "You don't have enough cash balance to complete this withdrawal."
        }

    if withdraw_status == "failing":
        transaction.status = "FAILED"
        transaction.save()
        return {
            "status": "error",
            "message": "Withdrawal failed. Please contact support."
        }

    elif withdraw_status == "pending":
        transaction.status = "PENDING"
        transaction.save()
        return {
            "status": "warning",
            "message": "Your withdrawal request is pending, if not processed within 24 hours contact support."
        }

    elif withdraw_status == "success":
        # ✅ Deduct balance ONLY here
        portfolio.cash_balance -= transaction.amount
        portfolio.save()

        transaction.balance = portfolio.cash_balance
        transaction.status = "SUCCESS"
        transaction.save()

        return {
            "status": "success",
            "message": "Withdrawal successful."
        }

    return {
        "status": "error",
        "message": "Invalid withdrawal status."
    }