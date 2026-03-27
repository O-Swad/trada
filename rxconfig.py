import reflex as rx


config = rx.Config(
    app_name="tradeoff_app",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)

