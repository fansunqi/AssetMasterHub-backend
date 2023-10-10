from django.urls import path, include
import User.views as views

urlpatterns = [
    # 用户登录登出
    path('/login', views.login),
    path('/logout', views.logout),
    path('/info/<str:sessionId>',views.user_info),
    # 系统管理员维护部门和员工
    path('/tree/<str:sessionId>',views.get_tree),
    path('/member/<str:sessionId>/<str:page_id>/<str:search_name>/<str:search_dep>/<str:search_auth>',views.get_all_member),
    path('/add',views.add_member),
    path('/remove/<str:sessionId>/<str:UserName>',views.remove_member),
    path('/lock',views.lock_member),
    path('/ChangeAuthority',views.change_authority),
    path('/RemakePassword',views.remake_password),
    path('/department/add',views.add_department),
    path('/department/<str:sessionId>/<str:DepartmentPath>/<str:page_id>/<str:search_name>/<str:search_auth>',views.get_next_department),
    path('/department/move',views.move_members),
    path('/department/delete/<str:sessionId>/<str:DepartmentPath>',views.delete_department),
    # 系统管理员管理应用与第三方url
    path('/App/<str:sessionId>/<str:authority>',views.manage_apps),
    path('/NewApp/<str:sessionId>/<str:authority>',views.get_apps),
    path('/App/delete/<str:sessionId>/<str:authority>/<str:appname>',views.delete_apps),
    # 资产相关
    path('/Asset_Detail/<str:sessionId>/<str:assetId>',views.get_asset_detail),
    path('/QR_Asset_Detail/<str:assetId>',views.QR_get_asset_detail),
    # 消息列表
    path('/Message/New/<str:sessionId>',views.get_new_message),
    path('/Message/All/<str:sessionId>/<str:page_id>/<str:search_read>',views.get_all_message),
    # 日志
    path('/Detail/<str:sessionId>/<str:page_type>/<str:page_id>/<str:search_succ>',views.get_log_detail),
    # 飞书对接
    path('/change_mobile',views.change_mobile),
    path('/feishu_login',views.feishu_login),
    path('/LeafDepartment/<str:sessionId>/<str:entityId>',views.get_leaf_department),
    path('/FeishuDepartment',views.change_feishu_department),
    path('/feishu_answer',views.return_feishu_answer),
    path('/feishu_sync',views.sync_feishu_member),
    path('/feishu_apply',views.manage_feishu_apply)
]
