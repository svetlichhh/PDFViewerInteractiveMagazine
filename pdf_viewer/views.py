# views.py
import json
import fitz
import pymupdf
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from .models import PDFDocument, Comment, Annotation, User as AnnotationUser
from rest_framework.exceptions import PermissionDenied
from .serializers import CommentSerializer, PDFDocumentSerializer


def ensure_annotation_user(django_user):
    if not django_user or not getattr(django_user, 'is_authenticated', False):
        return None
    annotation_user, _ = AnnotationUser.objects.get_or_create(id=django_user.id)
    return annotation_user

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()
    
    def get_queryset(self):
        # Фильтруем комментарии по PDF документу
        pdf_id = self.kwargs.get('pdf_id')
        if pdf_id:
            return Comment.objects.filter(pdf_id=pdf_id)
        if self.request.user.is_authenticated:
            return Comment.objects.filter(author_id=self.request.user.id)
        return Comment.objects.none()

    def perform_create(self, serializer):
        # Автоматически назначаем автора
        annotation_user = ensure_annotation_user(self.request.user)
        if annotation_user is None:
            raise PermissionDenied('Authentication required')
        serializer.save(author=annotation_user)

class PDFDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = PDFDocumentSerializer
    queryset = PDFDocument.objects.all()
    
    def get_queryset(self):
        # Показываем все документы (пока что)
        return PDFDocument.objects.all()
    
    def perform_create(self, serializer):
        # Автоматически назначаем владельца
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def get_pdf(self, request, pk=None):
        """Получить PDF документ"""
        pdf_document = self.get_object()
        try:
            # Открываем файл через storage system
            file = default_storage.open(pdf_document.pdf.name, 'rb')
            return FileResponse(file)
        except FileNotFoundError:
            return Response(
                {'error': 'File not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def annotations(self, request, pk=None):
        try:
            #"""Return annotation metadata with authorship details."""
            pdf_document = self.get_object()
            annotations = list(Annotation.objects.filter(pdf=pdf_document))
            current_user_id = request.user.id if request.user.is_authenticated else None

            annotation_user = ensure_annotation_user(request.user)
            if annotation_user:
                editor_color = annotation_user.annot_color
            else:
                editor_color = None

            author_ids = {annotation.author_id for annotation in annotations if annotation.author_id}
            auth_user_model = get_user_model()
            auth_users = auth_user_model.objects.filter(id__in=author_ids) if author_ids else []
            auth_user_map = {user.id: user for user in auth_users}

            data = []
            for annotation in annotations:
                auth_user = auth_user_map.get(annotation.author_id)
                data.append({
                    'id': annotation.id,
                    'xref': annotation.xref,
                    'author_id': annotation.author_id,
                    'author_username': getattr(auth_user, 'username', None) if auth_user else None,
                    'is_author': current_user_id is not None and annotation.author_id == current_user_id,
                })
            return Response({
                'annotations': data,
                'current_user_id': current_user_id,
                'editor_color': editor_color,
            })
        except Exception as e:
            print(e)
            return Response(
                {'error': 'An error occurred while fetching annotations'}, 
                status=500
            )

    #@action(detail=True, methods=['get'])
    #def download_annotated(self, request, pk=None):
    #    """Получить аннотированный PDF"""
    #    pdf_document = self.get_object()
    #    annotated_path = default_storage.path(f'annotated_{pdf_document.name}.pdf')
        
    #    try:
    #        return FileResponse(open(annotated_path, 'rb'))
    #    except FileNotFoundError:
    #        return Response(
    #            {'error': 'Annotated PDF not found'}, 
    #            status=status.HTTP_404_NOT_FOUND
    #        )
    
    @action(detail=True, methods=['post'])
    def add_annotation(self, request, pk=None):
        """Добавить аннотацию к PDF"""
        pdf_document = self.get_object()

        if not request.user.is_authenticated:
            return Response(
                {'status': 'error', 'message': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        annotation_user = ensure_annotation_user(request.user)
        if annotation_user is None:
            return Response(
                {'status': 'error', 'message': 'Unable to resolve annotation user'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
        
            with default_storage.open(pdf_document.pdf.name, 'rb') as f:
                data = f.read()
            
            doc = pymupdf.open(stream=data, filetype='pdf')
            
            # Получаем данные из запроса
            raw_page_num = request.data.get('page', 0)
            try:
                page_num = int(raw_page_num)
            except (TypeError, ValueError):
                page_num = 0

            try:
                title = request.data.get('title', 'юзернейм')
                quadpoints = list(request.data.get('quadpoints', {}).values())
                #div_height = request.data.get('divheight', 0)
                page = doc[page_num]
                # content = request.data.get('content', 'тестовый текст'))
                print('начальный список')
                print(quadpoints)
                quads_list = []
                for i in range(0, len(quadpoints), 8):
                    # Извлекаем 4 точки quadrilateral'а
                    x1, y1 = quadpoints[i], quadpoints[i+1]
                    x2, y2 = quadpoints[i+2], quadpoints[i+3] 
                    x3, y3 = quadpoints[i+4], quadpoints[i+5]
                    x4, y4 = quadpoints[i+6], quadpoints[i+7]
                    
                    # Создаем Quad для PyMuPDF
                    quad = fitz.Quad(
                        (x1, y1),  # возможно нужно инвертировать Y
                        (x2, y2),
                        (x3, y3), 
                        (x4, y4)
                    )
                    
                    quads_list.append(quad)

            except Exception as e:
                print(e)

            print('конечный список')
            print(quads_list)
            
            colors = {'stroke': self.convert_hexcolor(annotation_user.annot_color)}

            # СДЕЛАТЬ ЦВЕТА (set_colors должно помочь и при загрузке, при добавлении пока хз че делать)
        
            highlight = page.add_highlight_annot(quads=quads_list)
            
            highlight.set_info(title=title)#, content=content)
            highlight.set_colors(colors=colors)
            highlight.set_opacity(0) # для того чтобы цвет второй раз не отображался на документе 
            highlight.set_popup(rect=pymupdf.Rect(160, 180, 250, 150))
            highlight.set_open(False)
            highlight.update()

            model_annotation = Annotation(
                pdf=pdf_document,
                xref=highlight.xref,
                author=annotation_user,
            )
            model_annotation.save()
            
            # ПЕРЕЗАПИСЫВАЕМ оригинальный файл
            output_data = doc.write()
            doc.close()
            
            # Сохраняем обратно в тот же файл
            with default_storage.open(pdf_document.pdf.name, 'wb') as f:
                f.write(output_data)
            
            # Обновляем флаг в базе
            pdf_document.is_annotated = True
            pdf_document.save()
            # print(pdf_document.is_annotated)
            # print(model_annotation.id)
            
            return Response({
                'status': 'success',
                'message': 'Annotation added',
                'annotation': {
                    'id': model_annotation.id,
                    'xref': model_annotation.xref,
                    'author_id': model_annotation.author_id,
                    'author_username': getattr(request.user, 'username', None),
                    'is_author': True,
                    'editor_color': annotation_user.annot_color,
                },
                'current_user_id': request.user.id,
            })
            
        except Exception as e:
            print(e)
            return Response(
                {'status': 'error', 'message': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def delete_annotation(self, request, pk=None):

        pdf_document = self.get_object()

        if not request.user.is_authenticated:
            return Response(
                {'status': 'error', 'message': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        ensure_annotation_user(request.user)

        raw_page_num = request.data.get('page', 0)
        annotation_id_raw = request.data.get('annotation_id')
        if annotation_id_raw is None:
            return Response(
                {'status': 'error', 'message': 'annotation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        annotation_id_str = str(annotation_id_raw)
        if annotation_id_str.lower().endswith('r'):
            annotation_id_str = annotation_id_str[:-1]

        try:
            annot_xref = int(annotation_id_str)
        except (TypeError, ValueError):
            return Response(
                {'status': 'error', 'message': 'Invalid annotation identifier'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            page_num = int(raw_page_num)
        except (TypeError, ValueError):
            page_num = 0

        try:
            db_annot = Annotation.objects.get(pdf=pdf_document, xref=annot_xref)
        except Annotation.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Annotation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if db_annot.author_id and db_annot.author_id != request.user.id:
            return Response(
                {'status': 'error', 'message': 'You do not have permission to delete this annotation'},
                status=status.HTTP_403_FORBIDDEN
            )

        annotation_pk = db_annot.pk
        annotation_author_id = db_annot.author_id
        doc = None
        output_data = None

        try:
            with default_storage.open(pdf_document.pdf.name, 'rb') as f:
                data = f.read()
            doc = pymupdf.open(stream=data, filetype='pdf')

            page = doc[page_num]
            # Поиск аннотации по xref через итерацию — надёжно для любой страницы
            target_annot = None
            annot = page.first_annot
            while annot is not None:
                try:
                    if getattr(annot, 'xref', None) == annot_xref:
                        target_annot = annot
                        break
                finally:
                    annot = annot.next

            if target_annot is None:
                raise LookupError('annotation-missing')

            page.delete_annot(target_annot)
            output_data = doc.write()
        except LookupError:
            return Response(
                {'status': 'error', 'message': 'Annotation not found in PDF'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(e)
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if doc is not None:
                doc.close()

        if output_data is not None:
            with default_storage.open(pdf_document.pdf.name, 'wb') as f:
                f.write(output_data)

        db_annot.delete()

        return Response({
            'status': 'success',
            'message': 'Annotation deleted',
            'annotation': {
                'id': annotation_pk,
                'xref': annot_xref,
                'author_id': annotation_author_id,
            },
            'current_user_id': request.user.id,
        })
    
    def convert_hexcolor(self, hex_color):
        pymurgb = []
        hex_list = [hex_color[1:3], hex_color[3:5], hex_color[5:7]]
        
        for col in hex_list:
            pymurgb.append(int(col, 16) / 255)
        
        return pymurgb


# Обычная view для HTML интерфейса
def pdf_viewer_interface(request, pdf_id=None):
    """HTML интерфейс для просмотра PDF"""
    #context = {}
    #if pdf_id:
    #    pdf_document = get_object_or_404(PDFDocument, id=pdf_id, owner=request.user)
    #    context['pdf_document'] = pdf_document
    
    return render(request, 'pdf_viewer/mupdftest.html')
