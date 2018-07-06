# -*- coding: utf-8 -*-
#
#Copyright (C) 2010-2012, Yader Velasquez
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import re
from database import DataBase
from model import ComboBoxModel, TasksModel
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.activity.widgets import StopButton
from gettext import gettext as _
from datetime import date, datetime
import logging
from gi.repository import Pango

log = logging.getLogger('Calendario-Log')

class CalendarioActivity(activity.Activity):


    def __init__(self, handle):
        '''Constructor'''
        activity.Activity.__init__(self, handle)
        self.main_container = Gtk.HBox()
        toolbox = ToolbarBox()
        self.set_toolbar_box(toolbox)
        toolbox.show()
        self.path = self.get_activity_root()
        ###left side###
        self.left_container = Gtk.VBox()
        d = datetime.today()
        self.label_date = Gtk.Label(label=d.strftime("%d %B %Y"))
        self.calendar = Gtk.Calendar()
        self.calendar.connect('day-selected', self._day_selected_cb)
        self.calendar.connect('month-changed', self._mark_day_cb)
        self.calendar.connect('next-year', self._mark_day_cb)
        self.calendar.connect('prev-year', self._mark_day_cb)
        self.mark_day()

        self.tool_frame = Gtk.Frame()
        self.reminder_expander = Gtk.Expander()
        self.query_expander = Gtk.Expander()
        self.tool_box = Gtk.VBox()
        
        #reminder
        self.scroll_reminder = Gtk.ScrolledWindow()
        self.scroll_reminder.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll_reminder.set_size_request(-1, 170)
        self.reminder_list = Gtk.TreeView()
        self.scroll_reminder.add(self.reminder_list)
        self.reminder_expander.add(self.scroll_reminder)
        
        #query
        self.query_box = Gtk.VBox()
        self.label_q_priority = Gtk.Label(label=_("Priority"))
        self.label_q_category = Gtk.Label(label=_("Category"))

        comboBoxModel = ComboBoxModel()
        cat_model = comboBoxModel.get_category_model()
        pri_model = comboBoxModel.get_priority_model()
        cell = Gtk.CellRendererText()
       
        self.combobox_q_priority = Gtk.ComboBox()
        self.combobox_q_priority.pack_start(cell, True)
        self.combobox_q_priority.add_attribute(cell, 'text', 0)
        self.combobox_q_category = Gtk.ComboBox()
        self.combobox_q_category.pack_start(cell, True)
        self.combobox_q_category.add_attribute(cell, 'text', 0)
        self.combobox_q_category.set_model(cat_model)
        self.combobox_q_priority.set_model(pri_model)
        self.filter_button = Gtk.Button(_('Filter'))
        self.filter_button.connect('clicked', self._filter_query_cb)

        self.query_box.pack_start(self.label_q_priority, False, 0, 0)
        self.query_box.pack_start(self.combobox_q_priority, False, 0, 0)
        self.query_box.pack_start(self.label_q_category, False, 0, 0)
        self.query_box.pack_start(self.combobox_q_category, False, 0, 0)
        self.query_box.pack_start(self.filter_button, True, True, 5)
        self.query_expander.add(self.query_box)
        
        self.tool_box.pack_start(self.reminder_expander, False, 0, 0)
        self.tool_box.pack_start(self.query_expander, False, 0, 0)
        self.tool_frame.add(self.tool_box)
        self.left_container.pack_start(self.label_date, False, False, 5)
        self.left_container.pack_start(self.calendar, False, 0, 0)
        self.left_container.pack_start(self.tool_frame, True, True, 5)

        ###right side###
        self.right_container = Gtk.VBox()
        self.tasks_frame = Gtk.Frame()
        self.scroll_tasks = Gtk.ScrolledWindow()
        self.scroll_tasks.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.tasks_list = Gtk.TreeView()
        self.get_tasks()
        self.add_columns()
        self.scroll_tasks.add(self.tasks_list)
        self.tasks_frame.add(self.scroll_tasks)

        #options
        self.options_expander = Gtk.Expander()
        self.options_box = Gtk.HBox()
        self.label_b_priority = Gtk.Label(label=_("Priority"))
        self.combobox_priority = Gtk.ComboBox()
        self.combobox_priority.pack_start(cell, True)
        self.combobox_priority.add_attribute(cell, 'text', 0)
        self.label_b_category = Gtk.Label(label=_("Category"))
        self.combobox_category = Gtk.ComboBox()
        self.combobox_category.pack_start(cell, True)
        self.combobox_category.add_attribute(cell, 'text', 0)
        self.combobox_category.set_model(cat_model)
        self.combobox_priority.set_model(pri_model)
        
        self.priority_box = Gtk.VBox()
        self.priority_box.pack_start(self.label_b_priority, True, True, 0)
        self.priority_box.pack_start(self.combobox_priority, True, True, 0)
        self.category_box = Gtk.VBox()
        self.category_box.pack_start(self.label_b_category, True, True, 0)
        self.category_box.pack_start(self.combobox_category, True, True, 0)
        self.options_box.pack_start(self.category_box, True, True, 5)
        self.options_box.pack_start(self.priority_box, True, True, 5)
        self.options_expander.add(self.options_box)

        #input
        self.scroll_text = Gtk.ScrolledWindow()
        self.scroll_text.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.text_input = Gtk.TextView()
        self.text_input.set_size_request(0, 80)
        self.scroll_text.add(self.text_input)
        self.save_button = Gtk.Button(_("Add new"))
        self.save_button.connect('clicked', self._save_cb)
        self.remove_button = Gtk.Button(_("Remove"))
        self.remove_button.connect('clicked', self._delete_row_cb)
        self.buttons_box = Gtk.VBox()
        self.buttons_box.pack_start(self.save_button, False, 0, 0)
        self.buttons_box.pack_start(self.remove_button, False, 0, 0)
        self.input_box = Gtk.HBox()
        self.input_box.pack_start(self.scroll_text, True, True, 5)
        self.input_box.pack_start(self.buttons_box, False, 0, 0)


        self.right_container.pack_start(self.tasks_frame, True, True, 5)
        self.right_container.pack_start(self.options_expander, False, False, 0)
        self.right_container.pack_start(self.input_box, False, False, 5)

        self.main_container.pack_start(self.left_container, False, False, 5) 
        self.main_container.pack_start(self.right_container, True, True, 5)
        self.main_container.show_all()
        self.set_canvas(self.main_container)

    def get_tasks(self):
        '''Get the rows'''
        date_formated = date_format(self.calendar.get_date())
        db = DataBase(self.path)
        data = db.get(date_formated)
        reminder = db.get_reminder()
        db.close()
        tasks_model = TasksModel(data)
        reminder_model = TasksModel(reminder)
        self.tasks_list.set_model(tasks_model.get_model())
        self.reminder_list.set_model(reminder_model.get_model())

    def add_columns(self):
        '''Add columns to TreeView'''
        #for the tasks list
        cell_text = Gtk.CellRendererText() 
        titles = (_('Tasks'), _('Category'), _('Priority'))
        i = 1
        for title in titles:
            #if the colum is the first
            if i == 1:            
                column = Gtk.TreeViewColumn(title, cell_text, markup=i)
                #sizes commented are for emuler testing
                #column.set_min_width(300)
                column.set_min_width(440)
            else:
                column = Gtk.TreeViewColumn(title, cell_text, text=i)
                #column.set_min_width(100)
                column.set_min_width(135)
            self.tasks_list.append_column(column)
            i = i + 1

        cell_toggle = Gtk.CellRendererToggle()
        cell_toggle.connect('toggled', self._toggle_row_cb)
        column = Gtk.TreeViewColumn('', cell_toggle, active=4)
        self.tasks_list.append_column(column)

        #for the reminder
        column = Gtk.TreeViewColumn(titles[0], cell_text, text=1)
        self.reminder_list.append_column(column)
        column = Gtk.TreeViewColumn(titles[2], cell_text, text=3)
        self.reminder_list.append_column(column)

    def mark_day(self):
        '''Mark the days of the month with tasks'''
        date = date_format(self.calendar.get_date())
        #just the month
        data = (date[3:],) 
        db = DataBase(self.path)
        day_list = db.get_days(data)
        db.close()
        for i in day_list:
            self.calendar.mark_day(int(i))

    def _save_cb(self, widget, data=None):
        '''Save a task'''
        input_buffer = self.text_input.get_buffer()
        start, end = input_buffer.get_bounds()
        text = input_buffer.get_text(start, end, False).strip()
        text = strip_tag(text)
        
        if len(text) > 0:
            input_buffer.set_text('')
            category = self.combobox_category.get_active()
            priority = self.combobox_priority.get_active()
            self.combobox_category.set_active(-1)
            self.combobox_priority.set_active(-1)
            date_formated = date_format(self.calendar.get_date())
            data = (text, category, priority, 0, date_formated)
            db = DataBase(self.path)
            db.add(data)
            db.close()
            self.get_tasks()
            self.mark_day()

    def _toggle_row_cb(self, widget, path):
        '''Toggle button row'''
        model = self.tasks_list.get_model()
        row_iter = model.get_iter(path)
        #row is a Gtk.TreeModelRow()
        row = model[row_iter]
        row[4] = not row[4]
        #task, completed, id for the moment category and 
        #priority are excluded
        data = (row[4], row[0])
        db = DataBase(self.path)
        db.update(data)
        db.close()
        self.get_tasks()
        
    def _delete_row_cb(self, widget, data=None):
        '''Delete a row'''
        selection = self.tasks_list.get_selection()
        model, row_iter = selection.get_selected()
        row = model[row_iter]
        data = (row[0],)
        db = DataBase(self.path)
        db.delete(data)
        db.close()
        self.get_tasks()

    def _day_selected_cb(self, widget, data=None):
        '''Select new day'''
        date_formated = date_format(self.calendar.get_date())
        db = DataBase(self.path)
        data = db.get(date_formated)
        db.close()
        tasks_model = TasksModel(data)
        self.tasks_list.set_model(tasks_model.get_model())
    
    def _mark_day_cb(self, widget, data=None):
        '''Mark calendar days with bold font'''
        self.calendar.clear_marks()
        self.mark_day()

    def _filter_query_cb(self, widget, data=None):
        '''Query for filter the tasks'''
        category = self.combobox_q_category.get_active()
        priority = self.combobox_q_priority.get_active()
        self.combobox_q_category.set_active(-1)
        self.combobox_q_priority.set_active(-1)
        date_formated = date_format(self.calendar.get_date())
        data = (date_formated, category, priority)
        db = DataBase(self.path)
        tasks = db.filter_tasks(data)
        db.close()
        tasks_model = TasksModel(tasks)
        self.tasks_list.set_model(tasks_model.get_model())

    def close(self, skip_save=False):
        '''Override the close method'''
        activity.Activity.close(self, True)

    def read_file(self, filepath):
        pass

    def write_file(self, filepath):
        pass

class Task(object):
    '''Class represeting a task object'''
    def __init__(self, task_id, task, category, priority, completed):
        self.task_id = task_id;
        self.task = task
        self.category = category
        self.priority = priority
        self.completed = completed

    def get_task_id(self):
        return self.task_id

    def get_task(self):
        return self.task

    def get_category(self):
        return self.category

    def get_priority(self):
        return self.priority

    def get_complete(self):
        return self.completed

def date_format(cal_tuple):
    '''create a new format from the
    calendar get_date() return'''
    d = date(cal_tuple[0], cal_tuple[1] + 1, cal_tuple[2])
    return d.strftime("%d/%m/%Y")

def strike_string(string):
    '''Add pango markup'''
    return '<s>%s</s>' %(string)

def strip_tag(string):
    '''Delete all the tags'''
    return re.sub(r'<[^>]*?>', '', string)
