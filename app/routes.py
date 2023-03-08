def routes_list(app):
    # routes list

    # 메인 함수
    from .views import main_views
    app.register_blueprint(main_views.bp)

    return app