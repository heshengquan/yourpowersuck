from rest_framework import serializers

from pay.models import Goods, Address


class GoodsDetailSerializer(serializers.ModelSerializer):
    """
        商品详情序列化器
    """
    my_order_id = serializers.SerializerMethodField()
    express_fee = serializers.SerializerMethodField()

    def get_my_order_id(self,goods):
        return self.context['my_order_id']

    def get_express_fee(self,goods):
        return self.context['express_fee']

    class Meta:
        model = Goods
        fields = ('id','name','price','ever_price','description','amount_sold','amount_remain','express_fee','my_order_id')


class AddressSerializer(serializers.ModelSerializer):
    """
        某用户地址的列表序列化器
    """
    class Meta:
        model = Address
        fields = ('id','name','phone','province_name','city_name','county_name','detail_info',
                  'post_num','is_default')


class MonthRaceMembersSerializer(serializers.Serializer):
    """
        某月赛参与成员的列表序列化器
    """
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, order):
        return order.member_id.avatar_url