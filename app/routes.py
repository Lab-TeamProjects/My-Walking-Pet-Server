def routes_list(app):
    # routes list

    # 메인
    from .views import main_views
    app.register_blueprint(main_views.bp)

    # 회원가입, 로그인, 이메일 인증
    from .views import auth_views
    app.register_blueprint(auth_views.bp)

    return app