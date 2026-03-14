from rest_framework import serializers
from .models import PDFDocument, Comment, Annotation
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class CommentSerializer(serializers.ModelSerializer):
    author_info = UserSerializer(source='author', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'pdf', 'author', 'author_info', 'content', 'page', 'position', 'created_at']
        read_only_fields = ['author', 'created_at']

class PDFDocumentSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = PDFDocument
        fields = ['id', 'name', 'pdf', 'owner', 'comments']

class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = '__all__'