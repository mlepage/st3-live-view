# Live view plug-in for Sublime Text 3
# Copyright (c) 2013 Marc Lepage

import sublime, sublime_plugin
from subprocess import Popen, PIPE, STDOUT
from os.path import basename

# Command to run, may need full path or args
cmd = ['lua']

class lv_manager(object):
    def __init__(self):
        self.views = {}

    # get a live view for a view (may not exist)
    def get_live_view(self, view):
        view_id = view.id()
        if view_id in self.views:
            return self.views[view_id]
        return None

    # create a live view for a view
    def create_live_view(self, view):
        view_id = view.id()
        if view_id in self.views:
            return self.views[view_id]
        lv = view.window().new_file()
        lv.set_scratch(True)
        self.views[view_id] = lv
        return lv

    # destroy any live view for a view
    def destroy_live_view(self, view):
        view_id = view.id()
        if view_id in self.views:
            lv = self.views[view_id]
            lv.set_name(lv.name().replace(u'LIVE \u2014 ', u'live \u2014 '))
            del self.views[view_id]

    # deregister this potentially live view
    def deregister(self, view):
        for k, v in self.views.items():
            if v == view:
                del self.views[k]
                break

lv_mgr = lv_manager()

class lv_open_command(sublime_plugin.TextCommand):
    def run(self, edit):
        lv_mgr.create_live_view(self.view)
        self.view.run_command('lv_update')

class lv_close_command(sublime_plugin.TextCommand):
    def run(self, edit):
        lv_mgr.destroy_live_view(self.view)

class lv_update_command(sublime_plugin.TextCommand):
    def run(self, edit):
        lv = lv_mgr.get_live_view(self.view)
        input = self.view.substr(sublime.Region(0, self.view.size()))

        p = Popen(cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE)
        output, error = p.communicate(input.encode())

        name = self.view.file_name()
        if name:
            name = basename(name)
        else:
            name = 'untitled'

        if error:
            lv.set_name(u'live \u2014 ' + name)
            print(error.decode())
        else:
            lv.set_name(u'LIVE \u2014 ' + name)
            lv.replace(edit, sublime.Region(0, lv.size()), output.decode())

class lv_listener(sublime_plugin.EventListener):
    def on_modified_async(self, view):
        lv = lv_mgr.get_live_view(view)
        if lv:
            view.run_command('lv_update')
    def on_post_save_async(self, view):
        lv = lv_mgr.get_live_view(view)
        if lv:
            view.run_command('lv_update')
    def on_close(self, view):
        lv = lv_mgr.get_live_view(view)
        if lv:
            lv_mgr.destroy_live_view(view)
        else:
            lv_mgr.deregister(view)
