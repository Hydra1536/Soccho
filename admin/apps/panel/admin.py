from django.contrib import admin
from django.db import models


class User(models.Model):
    id = models.UUIDField(primary_key=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    google_sub = models.CharField(max_length=255, null=True, blank=True, unique=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True)
    lender_id = models.UUIDField()
    borrower_id = models.UUIDField()
    friendship_id = models.UUIDField()
    amount = models.TextField()
    due_date = models.TextField()
    status = models.CharField(max_length=16)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'transactions'


class Balance(models.Model):
    id = models.BigAutoField(primary_key=True)
    friendship_id = models.UUIDField(unique=True)
    net_balance = models.TextField()
    version = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'balances'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'created_at', 'loyalty_score')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)

    fields = ('username', 'email', 'loyalty_score')
    readonly_fields = ('loyalty_score',)
    exclude = ('password_hash',)

    def loyalty_score(self, obj):
        return '[ENCRYPTED]'

    loyalty_score.short_description = 'Loyalty Score'

    def get_queryset(self, request):
        return super().get_queryset(request).only('id', 'username', 'email', 'created_at')

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ('username', 'email', 'loyalty_score')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'lender_id', 'borrower_id', 'friendship_id', 'amount_masked', 'due_date_masked', 'status', 'is_deleted')
    readonly_fields = ('amount_masked', 'due_date_masked')
    fields = ('id', 'lender_id', 'borrower_id', 'friendship_id', 'amount_masked', 'due_date_masked', 'status', 'is_deleted', 'created_at')

    def amount_masked(self, obj):
        return '[ENCRYPTED]'

    amount_masked.short_description = 'Amount'

    def due_date_masked(self, obj):
        return '[ENCRYPTED]'

    due_date_masked.short_description = 'Due Date'

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'friendship_id', 'net_balance_masked', 'version')
    readonly_fields = ('net_balance_masked',)
    fields = ('id', 'friendship_id', 'net_balance_masked', 'version')

    def net_balance_masked(self, obj):
        return '[ENCRYPTED]'

    net_balance_masked.short_description = 'Net Balance'

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
