from app import bloodrooster_app, bloodrooster_socketapp
from flask import render_template, request, redirect, session
from app.webapp import BloodRoostrWebApp


webapp = BloodRoostrWebApp()


@bloodrooster_app.route("/")
def home():
    return redirect('/graph')


@bloodrooster_app.route("/graph", methods=['GET', 'POST'])
def graph():
    return render_template('index.html')


@bloodrooster_app.route("/graph_update", methods=['POST'])
def graph_update():
    graph_data = ''
    # test = '{"nodes":{"1":{"id":"test1", "name":"test1name", "type":"computer"},"2":{"id":"test2", "name":"test2name", "type":"user"},"3":{"id":"test3", "name":"test3name", "type":"group"}},"edges":{"1":{"id":1, "from":"test1","to":"test2"},"2":{"id":2, "from":"test2","to":"test3"},"3":{"id":3, "from":"test3","to":"test1"}}}'
    if request.method == 'POST':
        # print('Testing', request.get_data())
        # print('Testing2', request.get_json())
        graph_data = webapp.graph_update(request.get_json())
    return graph_data
