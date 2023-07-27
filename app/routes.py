from flask import Flask

def set_routes_list(app: Flask):
    # routes list

    # 메인
    from .views import main_views
    app.register_blueprint(main_views.bp)

    # 회원가입, 로그인, 이메일 인증
    from .views import account_views
    app.register_blueprint(account_views.bp)

    from .views import egg_views
    app.register_blueprint(egg_views.bp)

    from .views import friend_views
    app.register_blueprint(friend_views.bp)

    from .views import pet_views
    app.register_blueprint(pet_views.bp)

    from .views import store_views
    app.register_blueprint(store_views.bp)


    return app