# -*- coding:utf-8 -*-

import math, pymongo
from datetime import datetime
from bson import ObjectId
from functools import wraps
from flask import request, jsonify, request
from . import format_datetime
from ..views import render_json


def get_model(db, _id):
    if _id is None:
        model = db()
    else:
        model = db.get_from_id(_id)
    return model


def remove():
    def decorator(f):
        @wraps(f)
        def func():
            ids = request.form.get('ids')
            if not ids:
                return render_json(u'参数不能为空')
            try:
                ids = [ObjectId(_id) for _id in ids.split(',')]
            except Exception:
                return render_json(u'非法参数')
            return f(ids)
        return func
    return decorator


def clone_property(model, form, *keys):
    for k in keys:
        model[k] = form.get(k)

    return model


def get_table(models, ks=[], sort='_id'):
    '''获取列表
    ks:要显示的列名
    sort:默认排序的字段'''
    total = models.count()
    page, size, skip = get_page_size(total)
    data = []

    for m in models.sort(*get_sort(sort)).skip(skip).limit(size):
        l = {}
        for k in ks:
            if type(k) is type(''):
                k = [k]
            l['_'.join(k)] = _fmt(m, k)
        data.append(l)

    context = {
        'status': 1,
        'size': size,
        'total': total,
        'page': page,
        'data': data
    }
    return jsonify(context)


def get_entry(model, ks):
    data = {}

    for k in ks:
        if type(k) is type(''):
            k = [k]
        data['_'.join(k)] = _fmt(model, k)

    context = {
        'status': 1,
        'model': data
    }
    return jsonify(context)


_DATETIME = type(datetime.now())
_OBJECTID = type(ObjectId())
_NONE = type(None)
def _fmt(model, key):
    s = model
    for k in key:
        s = s[k]

    t = type(s)
    if t is _OBJECTID:
        s = str(s)
    elif t is _DATETIME:
        s = format_datetime(s)
    elif t is _NONE:
        s = 'None'

    return s


def get_page_size(total=1, size=20):
    '''获取分页页码和条目数'''
    try:
        page = int(request.json.get('page'))
    except Exception:
        page = 1

    try:
        _size = int(request.json.get('size'))
        if _size > 0:
            size = _size
    except Exception:
        size = size

    if page * size > total + size:
        page = int(math.ceil(total/float(size)))

    if page < 1:
        page = 1

    skip = (page-1) * size

    return page, size, skip


def get_filters(*args):
    '''获取查询筛选条件'''
    filters = {}
    for k in args:
        if request.form.get(k):
            filters.update({ k: {'$regex' : request.form.get(k)} })
    return filters


def get_sort(default_key="_id", default_sort=pymongo.ASCENDING, allow_key=None):
    '''生成排序条件'''
    sort_key = request.form.get('sort[key]')
    sort_order = pymongo.DESCENDING if request.form.get('sort[asc]') == "-1" else pymongo.ASCENDING
    if allow_key and sort_key in allow_key:
        return sort_key, sort_order
    elif allow_key is None and sort_key:
        return sort_key, sort_order
    else:
        return default_key, default_sort