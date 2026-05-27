from io import BytesIO
from math import ceil
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


class RDOPDFService:
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 26
    LEFT = MARGIN
    RIGHT = PAGE_WIDTH - MARGIN
    TOP = PAGE_HEIGHT - MARGIN
    BOTTOM = MARGIN
    ORANGE = colors.HexColor('#F3C744')
    LIGHT_GRAY = colors.HexColor('#E5E5E5')

    @classmethod
    def gerar_response(cls, rdo, inline=False):
        buffer = BytesIO()
        fotos = list(rdo.fotos.all())
        total_pages = 1 + max(1, ceil(len(fotos) / 6))

        pdf = canvas.Canvas(buffer, pagesize=A4)
        cls._draw_page_one(pdf, rdo, 1, total_pages)

        if fotos:
            for index in range(0, len(fotos), 6):
                pdf.showPage()
                page_number = 2 + index // 6
                cls._draw_photos_page(pdf, rdo, fotos[index:index + 6], page_number, total_pages)
        else:
            pdf.showPage()
            cls._draw_photos_page(pdf, rdo, [], 2, total_pages)

        pdf.save()

        data_rdo = cls._as_date(rdo.data)
        data_label = data_rdo.strftime('%Y-%m-%d') if data_rdo else 'sem_data'
        filename = f'RDO_{cls._slug(rdo.obra.nome)}_{data_label}_ND_{rdo.numero}.pdf'
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        disposition = 'inline' if inline else 'attachment'
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response

    @classmethod
    def _draw_page_one(cls, pdf, rdo, page_number, total_pages):
        header_bottom = cls._draw_header(pdf, rdo)
        y = header_bottom

        y = cls._draw_contract_row(pdf, rdo, y)
        y = cls._draw_date_row(pdf, rdo, y)
        y = cls._draw_workday_row(pdf, rdo, y)
        y = cls._draw_weather_row(pdf, rdo, y)
        y = cls._draw_two_column_section(
            pdf,
            'EFETIVO',
            ['Funcao', 'Presentes'],
            [(cls._efetivo_label(item), item.quantidade) for item in rdo.efetivos.all()],
            y,
            min_rows=6,
            footer=('Total de efetivo', cls._total_efetivo(rdo)),
        )
        y = cls._draw_two_column_section(
            pdf,
            'EQUIPAMENTOS',
            ['Equipamento', 'Presentes'],
            [(f'{item.nome_equipamento} | Hrs.: {cls._format_duration(item.horas_utilizadas)}', item.quantidade) for item in rdo.equipamentos.all()],
            y,
            min_rows=4,
        )
        y = cls._draw_accidents_row(pdf, rdo, y)
        cls._draw_activities(pdf, rdo, y)
        cls._draw_footer(pdf, page_number, total_pages)

    @classmethod
    def _draw_header(cls, pdf, rdo):
        y_top = cls.TOP
        height = 84
        y_bottom = y_top - height
        left_w = 150
        right_w = 150
        middle_left = cls.LEFT + left_w
        middle_right = cls.RIGHT - right_w

        cls._rect(pdf, cls.LEFT, y_bottom, cls.RIGHT - cls.LEFT, height)
        cls._line(pdf, middle_left, y_bottom, middle_left, y_top)
        cls._line(pdf, middle_right, y_bottom, middle_right, y_top)

        logo_path = Path(settings.BASE_DIR) / 'static' / 'img' / 'logo.jpg'
        if logo_path.exists():
            cls._draw_image_fit(pdf, str(logo_path), cls.LEFT + 52, y_bottom + 15, 48, 54)
        else:
            cls._center_text(pdf, 'I9', cls.LEFT, y_bottom + 30, left_w, 18, bold=True, size=24)

        cls._center_text(pdf, 'Relatorio Diario de Obra', middle_left, y_top - 22, middle_right - middle_left, 14, bold=True, size=14)
        cls._text(pdf, 'Obra:', middle_left + 8, y_top - 40, bold=True, size=7)
        cls._wrapped_text(pdf, rdo.obra.nome, middle_left + 42, y_top - 40, middle_right - middle_left - 50, 10, size=7)
        cls._text(pdf, 'Contrato:', middle_left + 8, y_top - 56, bold=True, size=7)
        cls._wrapped_text(pdf, rdo.obra.contrato or '-', middle_left + 52, y_top - 56, middle_right - middle_left - 60, 10, size=7)

        if rdo.obra.logo_cliente:
            try:
                cls._draw_image_fit(pdf, rdo.obra.logo_cliente.path, middle_right + 18, y_bottom + 15, right_w - 36, 54)
            except (OSError, ValueError):
                cls._center_text(pdf, rdo.obra.cliente or 'Contratante', middle_right, y_bottom + 33, right_w, 20, bold=True, size=16)
        else:
            cls._center_text(pdf, rdo.obra.cliente or 'Contratante', middle_right, y_bottom + 33, right_w, 20, bold=True, size=16)
        return y_bottom

    @classmethod
    def _draw_contract_row(cls, pdf, rdo, y_top):
        height = 18
        cols = [
            ('Contratante:', rdo.obra.cliente),
            ('Contratada:', 'I9tmg'),
            ('Responsavel I9:', rdo.obra.responsavel_i9 or '-'),
            ('Resp. cliente:', rdo.obra.responsavel_cliente or '-'),
        ]
        widths = [124, 96, 140, cls.RIGHT - cls.LEFT - 360]
        x = cls.LEFT
        for (label, value), width in zip(cols, widths):
            cls._cell(pdf, x, y_top - height, width, height, label, value)
            x += width
        return y_top - height

    @classmethod
    def _draw_date_row(cls, pdf, rdo, y_top):
        height = 18
        data_rdo = cls._as_date(rdo.data)
        data_inicio = cls._as_date(rdo.obra.data_inicio)
        data_fim = cls._as_date(rdo.obra.data_previsao_fim or rdo.obra.data_fim)
        dias_corridos = (data_rdo - data_inicio).days if data_rdo and data_inicio else '-'
        dias_restantes = (data_fim - data_rdo).days if data_fim and data_rdo else '-'
        cols = [
            ('Data:', data_rdo.strftime('%Y-%m-%d') if data_rdo else '-'),
            ('Dia da semana:', cls._weekday_pt(data_rdo) if data_rdo else '-'),
            ('Nr. Diario', rdo.numero),
            ('Inicio servicos', data_inicio.strftime('%Y-%m-%d') if data_inicio else '-'),
            ('Dias corridos', dias_corridos),
            ('Previsao fim', data_fim.strftime('%Y-%m-%d') if data_fim else '-'),
            ('Dias restantes', dias_restantes),
            ('Local', rdo.obra.local),
        ]
        widths = [58, 76, 54, 72, 68, 76, 78, cls.RIGHT - cls.LEFT - 482]
        x = cls.LEFT
        for (label, value), width in zip(cols, widths):
            cls._cell(pdf, x, y_top - height, width, height, label, value)
            x += width
        return y_top - height

    @classmethod
    def _draw_workday_row(cls, pdf, rdo, y_top):
        title_h = 18
        hour_h = 26
        third = (cls.RIGHT - cls.LEFT) / 3
        labels = [('Matutino', '07:00', '12:00'), ('Tarde', '13:00', '17:00'), ('Noturno', '', '')]

        for index, (period, entry, exit_) in enumerate(labels):
            x = cls.LEFT + third * index
            cls._rect(pdf, x, y_top - title_h, third, title_h, fill=cls.LIGHT_GRAY)
            cls._center_text(pdf, period, x, y_top - 12, third, 8, bold=True, size=7)
            cls._rect(pdf, x, y_top - title_h - hour_h, third, hour_h)
            cls._line(pdf, x + third / 2, y_top - title_h - hour_h, x + third / 2, y_top - title_h)
            cls._text(pdf, 'Entrada:', x + 5, y_top - title_h - 8, bold=True, size=7)
            cls._text(pdf, entry, x + 42, y_top - title_h - 20, size=7)
            cls._text(pdf, 'Saida:', x + third / 2 + 5, y_top - title_h - 8, bold=True, size=7)
            cls._text(pdf, exit_, x + third / 2 + 42, y_top - title_h - 20, size=7)
        return y_top - title_h - hour_h

    @classmethod
    def _draw_weather_row(cls, pdf, rdo, y_top):
        height = 44
        quarter = (cls.RIGHT - cls.LEFT) / 4
        data = [
            ('Manha', rdo.get_condicao_manha_display()),
            ('Tarde', rdo.get_condicao_tarde_display()),
            ('Noite', rdo.get_condicao_noite_display()),
            ('Chuva (mm)', '0.0'),
        ]
        for index, (label, value) in enumerate(data):
            x = cls.LEFT + quarter * index
            cls._rect(pdf, x, y_top - height, quarter, height)
            cls._text(pdf, label, x + 5, y_top - 12, bold=True, size=8)
            cls._wrapped_text(pdf, value, x + 5, y_top - 26, quarter - 10, 10, size=8)
        return y_top - height

    @classmethod
    def _draw_two_column_section(cls, pdf, title, headers, rows, y_top, min_rows, footer=None):
        title_h = 18
        header_h = 16
        row_h = 13
        rows = list(rows)
        rows_per_side = max(min_rows, ceil(len(rows) / 2))
        footer_h = row_h if footer else 0
        height = title_h + header_h + rows_per_side * row_h + footer_h
        y_bottom = y_top - height
        half = (cls.RIGHT - cls.LEFT) / 2
        name_w = half - 64

        cls._rect(pdf, cls.LEFT, y_top - title_h, cls.RIGHT - cls.LEFT, title_h, fill=cls.LIGHT_GRAY)
        cls._center_text(pdf, title, cls.LEFT, y_top - 13, cls.RIGHT - cls.LEFT, 8, bold=True, size=10)

        for side in range(2):
            x = cls.LEFT + side * half
            cls._rect(pdf, x, y_top - title_h - header_h, half, header_h, fill=cls.ORANGE)
            cls._line(pdf, x + name_w, y_bottom, x + name_w, y_top - title_h)
            cls._center_text(pdf, headers[0], x, y_top - title_h - 11, name_w, 8, bold=True, size=7)
            cls._center_text(pdf, headers[1], x + name_w, y_top - title_h - 11, 64, 8, bold=True, size=7)
            cls._rect(pdf, x, y_bottom, half, height - title_h)
            for idx in range(rows_per_side):
                y = y_top - title_h - header_h - idx * row_h
                cls._line(pdf, x, y - row_h, x + half, y - row_h)

        cls._line(pdf, cls.LEFT + half, y_bottom, cls.LEFT + half, y_top)

        for idx in range(rows_per_side * 2):
            if idx >= len(rows):
                continue
            side = 0 if idx < rows_per_side else 1
            row_index = idx if side == 0 else idx - rows_per_side
            x = cls.LEFT + side * half
            y = y_top - title_h - header_h - row_index * row_h - 10
            cls._text(pdf, str(rows[idx][0]), x + 3, y, size=6)
            cls._center_text(pdf, str(rows[idx][1]), x + name_w, y, 64, 6, size=6)

        if footer:
            y = y_bottom + 3
            cls._text(pdf, str(footer[0]), cls.LEFT + 4, y, bold=True, size=7)
            cls._text(pdf, str(footer[1]), cls.LEFT + 90, y, bold=True, size=7)

        return y_bottom

    @classmethod
    def _draw_accidents_row(cls, pdf, rdo, y_top):
        height = 20
        ca = rdo.ocorrencias.filter(tipo='SEGURANCA').count()
        sa = 0 if ca else 0
        cls._rect(pdf, cls.LEFT, y_top - height, cls.RIGHT - cls.LEFT, height)
        cls._text(pdf, 'Acidentes Ocorridos', cls.LEFT + 5, y_top - 13, bold=True, size=8)
        cls._line(pdf, cls.RIGHT - 106, y_top - height, cls.RIGHT - 106, y_top)
        cls._line(pdf, cls.RIGHT - 53, y_top - height, cls.RIGHT - 53, y_top)
        cls._center_text(pdf, 'C/A', cls.RIGHT - 106, y_top - 9, 53, 7, bold=True, size=7)
        cls._center_text(pdf, str(ca), cls.RIGHT - 106, y_top - 17, 53, 7, size=7)
        cls._center_text(pdf, 'S/A', cls.RIGHT - 53, y_top - 9, 53, 7, bold=True, size=7)
        cls._center_text(pdf, str(sa), cls.RIGHT - 53, y_top - 17, 53, 7, size=7)
        return y_top - height

    @classmethod
    def _draw_activities(cls, pdf, rdo, y_top):
        header_h = 18
        bottom = cls.BOTTOM + 36
        cls._rect(pdf, cls.LEFT, bottom, cls.RIGHT - cls.LEFT, y_top - bottom)
        cls._line(pdf, cls.LEFT, y_top - header_h, cls.RIGHT, y_top - header_h)
        cls._center_text(pdf, 'Atividades Realizadas', cls.LEFT, y_top - 13, cls.RIGHT - cls.LEFT, 8, bold=True, size=10)

        atividades = []
        for item in rdo.atividades.all():
            partes = [item.descricao]
            if item.local_execucao:
                partes.append(f'Execucao: {item.local_execucao}')
            if item.percentual_avanco is not None:
                partes.append(f'Avanco: {item.percentual_avanco}%')
            atividades.append(' | '.join(partes))
        if not atividades:
            atividades = [rdo.observacoes_gerais or '-']
        text = '\n'.join(atividades)
        cls._wrapped_text(pdf, text, cls.LEFT + 10, y_top - header_h - 12, cls.RIGHT - cls.LEFT - 20, y_top - header_h - bottom - 12, size=8)

    @classmethod
    def _draw_photos_page(cls, pdf, rdo, fotos, page_number, total_pages):
        header_bottom = cls._draw_header(pdf, rdo)
        y = cls._draw_date_row(pdf, rdo, header_bottom)
        gap = 8
        grid_top = y - 10
        col_gap = 6
        row_gap = 6
        box_w = (cls.RIGHT - cls.LEFT - col_gap) / 2
        box_h = 164
        start_y = grid_top

        for idx in range(6):
            col = idx % 2
            row = idx // 2
            x = cls.LEFT + col * (box_w + col_gap)
            y_top = start_y - row * (box_h + row_gap)
            foto = fotos[idx] if idx < len(fotos) else None
            cls._draw_photo_box(pdf, x, y_top - box_h, box_w, box_h, idx + 1 + (page_number - 2) * 6, foto, rdo)

        signature_y = cls.BOTTOM + 28
        sig_w = (cls.RIGHT - cls.LEFT) / 3
        labels = ['Responsavel I9', 'Responsavel cliente', 'Responsavel RDO']
        values = [rdo.obra.responsavel_i9, rdo.obra.responsavel_cliente, rdo.responsavel]
        for idx in range(3):
            x = cls.LEFT + idx * sig_w
            cls._rect(pdf, x, signature_y, sig_w, 42)
            cls._center_text(pdf, labels[idx], x, signature_y + 28, sig_w, 8, bold=True, size=7)
            cls._center_text(pdf, values[idx] or '-', x, signature_y + 12, sig_w, 8, size=7)

        cls._draw_footer(pdf, page_number, total_pages)

    @classmethod
    def _draw_photo_box(cls, pdf, x, y, width, height, number, foto, rdo):
        meta_h = 30
        label_h = 10
        image_h = height - meta_h - label_h
        area = rdo.obra.local if foto else ''
        legenda = foto.legenda if foto else ''

        cls._rect(pdf, x, y + height - meta_h, width, meta_h)
        cls._line(pdf, x, y + height - 15, x + width, y + height - 15)
        cls._text(pdf, 'Area:', x + 4, y + height - 10, bold=True, size=6)
        cls._text(pdf, area, x + 34, y + height - 10, size=6)
        cls._text(pdf, f'Foto {number}:', x + 4, y + height - 25, bold=True, size=6)
        cls._wrapped_text(pdf, legenda, x + 42, y + height - 24, width - 48, 8, size=6)
        cls._rect(pdf, x, y + image_h, width, label_h)
        cls._text(pdf, f'Photo {number}', x + 2, y + image_h + 2, size=5)
        cls._rect(pdf, x, y, width, image_h)

        image_path = cls._photo_path(foto)
        if image_path:
            try:
                cls._draw_image_fit(pdf, image_path, x + 4, y + 4, width - 8, image_h - 8)
            except OSError:
                cls._line(pdf, x, y + image_h, x + width, y)
        else:
            cls._line(pdf, x, y + image_h, x + width, y)

    @classmethod
    def _draw_footer(cls, pdf, page_number, total_pages):
        cls._text(pdf, f'{page_number}/{total_pages}', cls.RIGHT - 14, cls.BOTTOM - 6, size=7)

    @classmethod
    def _cell(cls, pdf, x, y, width, height, label, value):
        cls._rect(pdf, x, y, width, height)
        cls._center_text(pdf, label, x, y + height - 8, width, 6, bold=True, size=6)
        cls._center_text(pdf, str(value or '-'), x, y + 4, width, 7, size=7)

    @staticmethod
    def _slug(value):
        return ''.join(char if char.isalnum() else '_' for char in value).strip('_')

    @staticmethod
    def _as_date(value):
        if not value:
            return None
        if hasattr(value, 'strftime'):
            return value
        return parse_date(str(value))

    @staticmethod
    def _weekday_pt(date_value):
        names = ['segunda-feira', 'terca-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sabado', 'domingo']
        return names[date_value.weekday()]

    @staticmethod
    def _photo_path(foto):
        if not foto or not foto.imagem:
            return None
        if foto.imagem_pdf:
            return foto.imagem_pdf.path

        foto.gerar_imagem_pdf(save=True)
        if foto.imagem_pdf:
            return foto.imagem_pdf.path
        return foto.imagem.path

    @staticmethod
    def _total_efetivo(rdo):
        return sum(item.quantidade or 0 for item in rdo.efetivos.all())

    @classmethod
    def _efetivo_label(cls, item):
        entrada = item.horario_entrada.strftime('%H:%M') if item.horario_entrada else '-'
        return f'{item.nome_funcao} | Ent.: {entrada} | Hrs.: {cls._format_duration(item.horas_trabalhadas)}'

    @staticmethod
    def _format_duration(value):
        if not value:
            return '-'
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return f'{hours:02d}:{minutes:02d}'

    @classmethod
    def _rect(cls, pdf, x, y, width, height, fill=None):
        if fill:
            pdf.setFillColor(fill)
            pdf.rect(x, y, width, height, stroke=1, fill=1)
            pdf.setFillColor(colors.black)
        else:
            pdf.rect(x, y, width, height, stroke=1, fill=0)

    @staticmethod
    def _line(pdf, x1, y1, x2, y2):
        pdf.line(x1, y1, x2, y2)

    @staticmethod
    def _text(pdf, text, x, y, bold=False, size=8):
        pdf.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        pdf.drawString(x, y, str(text or ''))

    @staticmethod
    def _center_text(pdf, text, x, y, width, height, bold=False, size=8):
        pdf.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        pdf.drawCentredString(x + width / 2, y, str(text or ''))

    @staticmethod
    def _wrapped_text(pdf, text, x, y, width, max_height, size=8, leading=None):
        leading = leading or size + 2
        pdf.setFont('Helvetica', size)
        available_lines = max(1, int(max_height / leading))
        lines = []
        for raw_line in str(text or '').splitlines():
            words = raw_line.split()
            line = ''
            for word in words:
                candidate = f'{line} {word}'.strip()
                if pdf.stringWidth(candidate, 'Helvetica', size) <= width:
                    line = candidate
                else:
                    if line:
                        lines.append(line)
                    line = word
            lines.append(line)
        for index, line in enumerate(lines[:available_lines]):
            pdf.drawString(x, y - index * leading, line)

    @staticmethod
    def _draw_image_fit(pdf, image_path, x, y, width, height):
        reader = ImageReader(image_path)
        image_width, image_height = reader.getSize()
        scale = min(width / image_width, height / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale
        pdf.drawImage(
            reader,
            x + (width - draw_width) / 2,
            y + (height - draw_height) / 2,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask='auto',
        )
