from django.urls import path, include
import Asset.views as views

urlpatterns = [
    path('/tree', views.give_tree), 
    path('/add_data/<str:asset_class_name>/<int:i>/<int:j>/<int:k>', views.add_data), 
    path('/add_asset_class/<int:i>/<int:j>/<int:k>', views.add_asset_class_url),
    path('/modify_department/<int:i>', views.modify_department),
    path('/Create', views.superuser_create),
    path('/Delete/<str:SessionID>/<str:EntityName>', views.superuser_delete, name="superuser_delete"),
    path('/info/<str:SessionID>', views.superuser_info),
    path('/AddAssetClass', views.add_asset_class),
    path('/ModifyAssetClass', views.modify_asset_class),
    path('/DeleteAssetClass/<str:SessionID>/<int:NodeValue>', views.delete_asset_class),
    path('/Append/<str:SessionID>', views.add_asset),
    path('/Info/<str:SessionID>', views.asset_info),
    path('/Apply/<str:SessionID>', views.asset_apply),
    path('/Approval/<str:SessionID>', views.asset_approval),
    path('/DepartmentTree', views.give_department_tree),
    path('/Change/<str:SessionID>', views.asset_change),
    path('/Manage/<str:SessionID>', views.asset_manage),
    path('/DefineProp/<str:SessionID>', views.define_prop),
    path('/AppendType/<str:SessionID>/<str:Type>', views.asset_append_type), 
    path('/InfoProp/<str:SessionID>/<str:Prop>/<str:PropValue>', views.info_prop),
    path('/Label/<str:SessionID>/<str:AssetID>', views.modify_label),
    path('/MutiAppend/<str:SessionID>', views.asset_multi_append),
    # 资产统计
    path('/StatisticsRealFast/<str:SessionID>', views.asset_statistics_real_fast), 
    path('/StatisticsFast/<str:SessionID>', views.asset_statistics_fast),
    path('/StatisticsSlow/<str:SessionID>', views.asset_statistics_slow),
    path('/Statistics/<str:SessionID>', views.asset_statistics),
    # 用户更改信息
    path('/ChangePassword/<str:SessionID>', views.user_change_password),
    # 资产告警
    path('/Warn/<str:SessionID>/<int:PageType>/<int:PageId>/<str:SearchName>/<str:AssetType>/<str:WarnType>', views.asset_warn),
    path('/UserWarn/<str:SessionID>/<int:PageType>/<int:PageId>/<str:SearchName>/<str:AssetType>/<str:WarnType>', views.user_asset_warn),
    path('/Warn/<str:SessionID>', views.asset_warn_set),
    # 资产信息的搜索
    path('/Info/<str:SessionID>/<int:PageID>/<str:SearchID>/<str:SearchName>/<str:SearchClass>/<str:SearchStatus>/<str:SearchOwner>/<str:SearchProp>/<str:SearchPropValue>', views.info_search)

]
