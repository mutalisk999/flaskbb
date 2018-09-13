# -*- coding: utf-8 -*-
"""
    flaskbb.forum.forms
    ~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the forum views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from flask_wtf import FlaskForm
from wtforms import (TextAreaField, StringField, SelectMultipleField,
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length

from flask import current_app
from flask_babelplus import lazy_gettext as _

from flaskbb.forum.models import Topic, Post, Report, Forum
from flaskbb.user.models import User


logger = logging.getLogger(__name__)


class PostForm(FlaskForm):
    content = TextAreaField(_("Content"), validators=[
        DataRequired(message=_("You cannot post a reply without content."))])

    submit = SubmitField(_("Reply"))

    def save(self, user, topic):
        post = Post(content=self.content.data)
        current_app.pluggy.hook.flaskbb_form_new_post_save(form=self)
        return post.save(user=user, topic=topic)


class QuickreplyForm(PostForm):
    pass


class ReplyForm(PostForm):
    track_topic = BooleanField(_("Track this topic"), default=False,
                               validators=[Optional()])

    def save(self, user, topic):
        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        return super(ReplyForm, self).save(user, topic)


class TopicForm(FlaskForm):
    title = StringField(_("Topic title"), validators=[
        DataRequired(message=_("Please choose a title for your topic."))])

    content = TextAreaField(_("Content"), validators=[
        DataRequired(message=_("You cannot post a reply without content."))])

    track_topic = BooleanField(_("Track this topic"), default=False,
                               validators=[Optional()])

    submit = SubmitField(_("Post topic"))

    def save(self, user, forum):
        topic = Topic(title=self.title.data, content=self.content.data)

        if self.track_topic.data:
            user.track_topic(topic)
        else:
            user.untrack_topic(topic)

        current_app.pluggy.hook.flaskbb_form_new_topic_save(form=self,
                                                            topic=topic)
        return topic.save(user=user, forum=forum)


class NewTopicForm(TopicForm):
    pass


class EditTopicForm(TopicForm):
    def populate_obj(self, *objs):
        """
        Populates the attributes of the passed `obj`s with data from the
        form's fields. This is especially useful to populate the topic and
        post objects at the same time.
        """
        for obj in objs:
            super(EditTopicForm, self).populate_obj(obj)


class ReportForm(FlaskForm):
    reason = TextAreaField(_("Reason"), validators=[
        DataRequired(message=_("What is the reason for reporting this post?"))
    ])

    submit = SubmitField(_("Report post"))

    def save(self, user, post):
        report = Report(reason=self.reason.data)
        return report.save(post=post, user=user)


class UserSearchForm(FlaskForm):
    search_query = StringField(_("Search"), validators=[
        DataRequired(), Length(min=3, max=50)
    ])

    submit = SubmitField(_("Search"))

    def get_results(self):
        query = self.search_query.data
        return User.query.whooshee_search(query)


class SearchPageForm(FlaskForm):
    search_query = StringField(_("Criteria"), validators=[
        DataRequired(), Length(min=3, max=50)])

    search_types = SelectMultipleField(_("Content"), validators=[
        DataRequired()], choices=[('post', _('Post')), ('topic', _('Topic')),
                                  ('forum', _('Forum')), ('user', _('Users'))])

    submit = SubmitField(_("Search"))

    def get_results(self):
        # Because the DB is not yet initialized when this form is loaded,
        # the query objects cannot be instantiated in the class itself
        search_actions = {
            'post': Post.query.whooshee_search,
            'topic': Topic.query.whooshee_search,
            'forum': Forum.query.whooshee_search,
            'user': User.query.whooshee_search
        }

        query = self.search_query.data
        types = self.search_types.data
        results = {}

        for search_type in search_actions.keys():
            if search_type in types:
                results[search_type] = search_actions[search_type](query)

        return results
