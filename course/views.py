from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Course
from .serializers import CourseSerializer
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView

from rest_framework import generics

from rest_framework import viewsets

from django.db.models.signals import post_save
from django.dispatch import receiver

# 导入 Django 的 User 模型类
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.authtoken.models import Token

from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication

from .permissions import IsOwnerOrReadOnly


@receiver(post_save, sender=settings.AUTH_USER_MODEL)  # Django 信号机制
def generate_token(sender, instance=None, created=False, **kwargs):
    """
    创建用户时自动生成Token
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    if created:
        Token.objects.create(user=instance)


"""一、函数式编程 FBV"""


@api_view(["GET", "POST"])
@authentication_classes((BasicAuthentication, SessionAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def course_list(request):
    """
    获取所有课程信息或新增一个课程
    :param request:
    :return:
    """
    if request.method == "GET":
        s = CourseSerializer(instance=Course.objects.all(), many=True)
        return Response(data=s.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        s = CourseSerializer(data=request.data)  # 部分更新可用 partial=True 属性
        if s.is_valid():
            s.save(teacher=request.user)
            return Response(data=s.data, status=status.HTTP_201_CREATED)
        return Response(data=s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes((BasicAuthentication, SessionAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def course_detail(request, pk):
    """
    获取、更新、删除一个课程
    :param request:
    :param pk:
    :return:
    """

    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"msg": "没有此课程信息"}, status=status.HTTP_404_NOT_FOUND)
    else:
        if request.method == "GET":
            s = CourseSerializer(instance=course)
            return Response(data=s.data, status=status.HTTP_200_OK)
        if request.method == "PUT":
            s = CourseSerializer(instance=course, data=request.data)
            if s.is_valid():
                s.save()
                return Response(data=s.data, status=status.HTTP_200_OK)
        if request.method == "DELETE":
            course.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


"""二、类视图编程 CBV"""


class CourseList(APIView):
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication)

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        :param request:
        :return:
        """
        querySet = Course.objects.all()
        s = CourseSerializer(instance=querySet, many=True)
        return Response(data=s.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        :param request:
        :return:
        """
        s = CourseSerializer(data=request.data)
        if s.is_valid():
            s.save(teacher=request.user)
            return Response(data=s.data, status=status.HTTP_201_CREATED)
        return Response(data=s.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDetail(APIView):

    @staticmethod
    def get_object(pk):
        try:
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return

    def get(self, request, pk):
        """

        :param request:
        :param pk:
        :return:
        """
        obj = self.get_object(pk=pk)
        if not obj:
            return Response(data={"msg": "没有此课程信息"}, status=status.HTTP_404_NOT_FOUND)

        s = CourseSerializer(instance=obj)
        return Response(data=s.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """

        :param request:
        :param pk:
        :return:
        """
        obj = self.get_object(pk=pk)
        if not obj:
            return Response(data={"msg": "没有此课程信息"}, status=status.HTTP_404_NOT_FOUND)

        s = CourseSerializer(instance=obj, data=request.data)
        if s.is_valid():
            s.save()
            return Response(data=s.data, status=status.HTTP_201_CREATED)

        return Response(data=s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """

        :param request:
        :param pk:
        :return:
        """
        obj = self.get_object(pk=pk)
        if not obj:
            return Response(data={"msg": "没有此课程信息"}, status=status.HTTP_404_NOT_FOUND)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


"""三、通用类视图 GCBV"""


class GCourseList(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class GCourseDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


"""四、DRF 的视图集 viewsets"""


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

# from django.shortcuts import render
#
# import json
# from django.http import JsonResponse, HttpResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
#
# from django.views import View
#
# # Create your views here.
# course_dict = {
#     'name': '课程名称',
#     'introduction': '课程介绍',
#     'price': 0.11
# }
#
#
# # Django 原生 FBV 编写 API 接口
# @csrf_exempt
# def course_list(request):
#     if request.method == 'GET':
#         # return HttpResponse(json.dumps(course_dict), content_type='application/json')  # 这两种写法作用一样
#         return JsonResponse(course_dict)
#
#     if request.method == 'POST':
#         course = JsonResponse(request.body.decode('utf-8'))
#         # return JsonResponse(course, safe=False)
#         return HttpResponse(json.dumps(course), content_type='application/json')
#
#
# # Django 原生 CBV 编写 API 接口
# @method_decorator(csrf_exempt, name='dispatch')
# class CourseList(View):
#
#     def get(self, request):
#         return JsonResponse(course_list)
#
#     def post(self, request):
#         course = json.loads(request.body.decode('utf-8'))
#         return HttpResponse(json.dumps(course), content_type='application/json')
