from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.db.models import Count, Case, When, IntegerField, Sum
from django_object_actions import DjangoObjectActions


from . import models

user_model = get_user_model()


class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    extra = 2
    max_num = 4
    min_num = 1


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'get_title_image', 'pk', 'name', 'category', 'regular_price',
        'selling_price', 'status', 'created_at', 'updated_at',
    )
    list_display_links = (
        'get_title_image', 'pk', 'name', 'category', 'regular_price',
        'selling_price', 'status', 'created_at', 'updated_at',
    )
    inlines = (ProductImageInline, )
    list_filter = ('category', 'status', )
    search_fields = ('name', 'selling_price', )
    date_hierarchy = 'updated_at'

    def get_title_image(self, obj):
        image = obj.productimage_set.order_by('pk').first()
        if not image:
            return ''
        return mark_safe(
            f'<img src="{image.content.url}" style="width: 50px;">'
        )
    get_title_image.short_description = _('제품 이미지')


class ProductOrderInline(admin.StackedInline):
    model = models.Order.items.through
    min_num = 1


def change_progress_to_ongoing_delivery(modeladmin, request, queryset):
    queryset.update(progress='ongoing_delivery')
    messages.success(request, _('배송 상태로 변경했습니다.'))


change_progress_to_ongoing_delivery.short_description = _('배송 상태로 변경')


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'get_short_sn', 'user', 'product_cost', 'progress',
        'created_at', 'updated_at',
    )
    list_display_links = (
        'get_short_sn', 'user', 'product_cost', 'progress',
        'created_at', 'updated_at',
    )
    readonly_fields = ('user', 'product_cost', 'comment', )
    actions = (change_progress_to_ongoing_delivery, )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = user_model.objects.filter(username='hannal')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_short_sn(self, obj):
        return obj.sn.hex[:8]
    get_short_sn.short_description = _('짧은 주문번호')


class UserOrderCountFilter(admin.SimpleListFilter):
    title = _('구매횟수')
    parameter_name = 'order_count'

    def lookups(self, request, model_admin):
        return (
            ('exact-0', _('없음'), ),
            ('exact-1', _('1회'), ),
            ('exact-2', _('2회'), ),
            ('exact-3', _('3회'), ),
            ('gt-3', _('3회 초과'), ),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        try:
            lookup_keyword, count = value.split('-')
            count = int(count)
        except ValueError:
            return queryset.none()
        if count == 0:
            users = models.Order.objects \
                .filter(progress='done') \
                .values_list('user__id')
            return queryset.exclude(pk__in=users)

        lookups = {
            f'cnt__{lookup_keyword}': count,
        }
        return queryset \
            .annotate(cnt=Count(
                Case(
                    When(order__progress='done', then=0),
                    output_field=IntegerField()
                )
            )).filter(**lookups)


class SumOrderCostFilter(admin.SimpleListFilter):
    title = _('누적 구매총액')
    parameter_name = 'order_cost'

    def lookups(self, request, model_admin):
        return (
            ('lt-50000', _('5만원 미만'), ),
            ('gte-50000--lt-100000', _('5만원 이상 10만원 미만'), ),
            ('gte-100000--lt-200000', _('10만원 이상 20만원 미만'), ),
            ('gte-200000--lt-500000', _('20만원 이상 50만원 미만'), ),
            ('gte-500000', _('50만원 이상'), ),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        try:
            l1, l2 = value.split('--')
        except ValueError:
            l1, l2 = value, None

        lookups = {}
        for l in (l1, l2):
            if not l:
                continue
            try:
                lookup_keyword, amount = l.split('-')
                lookups[f'cost__{lookup_keyword}'] = int(amount)
            except ValueError:
                continue

        if not lookups:
            return queryset.none()
        return queryset.filter(order__progress='done') \
            .annotate(cost=Sum('order__product_cost')).filter(**lookups)


admin.site.unregister(User)


@admin.register(user_model)
class CustomUserAdmin(DjangoObjectActions, UserAdmin):
    list_display = UserAdmin.list_display + ('get_registration_route', )
    list_filter = (
        'profile__registration_route',
        UserOrderCountFilter, SumOrderCostFilter,
    )
    change_actions = ('make_user_happy', )
    list_per_page = 1
    list_max_show_all = 1000000

    def make_user_happy(self, request, obj):
        messages.info(request, f'{obj}님을 행복하게 했습니다.')
        # do something
    make_user_happy.label = _('이용자 행복하게 하기')
    make_user_happy.short_description = _('이용자 행복하게 하기')

    def get_registration_route(self, obj):
        try:
            return obj.profile.get_registration_route_display()
        except models.Profile.DoesNotExist:
            return '?'
    get_registration_route.short_description = _('가입경로')
