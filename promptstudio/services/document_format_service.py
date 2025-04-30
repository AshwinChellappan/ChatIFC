from core.config import settings
from util.logger import Logger
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
import markdown2
from bs4 import BeautifulSoup
from util.constants import MISC
import roman

logger = Logger()

class DocumentFormatService:

    def __init__(self, response_template = False):
        logger.log('Initiate instantiation of Document Format Service...')
        self.styles = None

    def apply_header_formatting(self, doc, element, insert_after_paragraph):
        new_paragraph = doc.add_paragraph(element.get_text())
        new_paragraph.style = f'Heading {element.name[-1]}'
        new_paragraph.paragraph_format.left_indent = Pt(18)
        insert_after_paragraph._element.addnext(new_paragraph._element)
        insert_after_paragraph = new_paragraph

        return doc, insert_after_paragraph

    def has_children(self, child):
        has_children = False
        try:
            children = list(child.children)
            if children:
                has_children = True
        except AttributeError as error:
            has_children = False

        return has_children

    def apply_para_formatting(self, doc, element, insert_after_paragraph, stylized_elements):
        all_styles = []
        skip_list = []
        # Add a blank paragraph
        new_paragraph = doc.add_paragraph('')
        # check if element has children
        if self.has_children(element):
            new_paragraph, skip_list, prefix, all_styles = self.process_tree(element, new_paragraph, skip_list, all_styles = all_styles, level = 1)
        else:
            run = new_paragraph.add_run(element.get_text())
            run = self.add_doc_style(run, all_styles)
            run.font.size = Pt(12)
        new_paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        new_paragraph.paragraph_format.line_spacing = 1.15
        new_paragraph.paragraph_format.space_after = Pt(5)
        insert_after_paragraph._element.addnext(new_paragraph._element)
        insert_after_paragraph = new_paragraph

        return doc, insert_after_paragraph

    def insert_list_para(self, list_element, insert_after_paragraph, doc, para_text, skip_list, indent_level = 1, prefix = ''):
        all_styles = []
        new_paragraph = doc.add_paragraph()
        if self.has_children(list_element):
            new_paragraph, skip_list, prefix, all_styles = self.process_tree(list_element, new_paragraph, skip_list, all_styles = all_styles, level = 1, prefix = prefix)
        else:
            run = new_paragraph.add_run(f'{prefix}{para_text}')
            run = self.add_doc_style(run, all_styles)
        new_paragraph.style = MISC.DOC_STYLE_LB
        # Set the indentation level
        new_paragraph.paragraph_format.left_indent = Pt(18 * indent_level)
        insert_after_paragraph._element.addnext(new_paragraph._element)
        insert_after_paragraph = new_paragraph

        return insert_after_paragraph, skip_list

    def add_style(self, all_styles, element_name):
        if element_name in ['em', 'strong', 'code']:
            all_styles.append(element_name)

        return all_styles

    def process_tree(self, element, new_paragraph, skip_list, all_styles = [], level = 1, prefix = ''):
        for child in element.children:
            element_styles = all_styles.copy()
            element_styles = self.add_style(element_styles, child.name)
            if child.name in ['ul', 'ol']:
                break
            if self.has_children(child):
                new_level = level + 1
                new_paragraph, skip_list, prefix, element_styles = self.process_tree(child, new_paragraph, skip_list, all_styles = element_styles, level = new_level, prefix = prefix)
            else:
                if child.name is None and child.get_text()[-2:] == '\n':
                    child_text = ''
                else:
                    child_text = f'{prefix}{child.get_text()}'
                run = new_paragraph.add_run(child_text)
                run.font.size = Pt(12)
                prefix = ''
                run = self.add_doc_style(run, element_styles)
                skip_list.append(child)
        
        return new_paragraph, skip_list, prefix, element_styles

    def apply_list_formatting(self, element, doc, insert_after_paragraph, num_list = False):
        skip_list = []
        baby_list = []
        nested_list = []
        # Level 1 list
        for l1_idx, list_element in enumerate(element.find_all('li')):
            if list_element.get_text() == '\n':
                continue
            if l1_idx == 0:
                parent_sr_no = l1_idx + 1
            elif list_element not in skip_list:
                parent_sr_no += 1
            nested_list = list_element.find(['ul', 'ol'], recursive = False)
            if nested_list is None:
                nested_list = []
            baby_list.append(nested_list)
            l1_prefix = f'{str(parent_sr_no)}. ' if num_list else '- '
            # If it's not a leaf element
            if list_element not in skip_list and nested_list:
                doc, insert_after_paragraph, skip_list = self.apply_nested_list_formatting(list_element, nested_list, doc, insert_after_paragraph, prefix = l1_prefix, skip_list = skip_list, indent_level = 1, num_list = False)
            # IF it's a leaf element
            elif list_element not in skip_list:
                para_text = l1_prefix + list_element.get_text()
                insert_after_paragraph, skip_list = self.insert_list_para(list_element, insert_after_paragraph, doc, para_text, skip_list, indent_level = 1, prefix = l1_prefix)
            
        return doc, insert_after_paragraph, baby_list

    def apply_nested_list_formatting(self, list_element, nested_list, doc, insert_after_paragraph, prefix = '', skip_list = None, indent_level = 1, num_list = False):
        if skip_list is None:
            skip_list = []
        l1_prefix = prefix
        # If it's not a leaf element
        if list_element in skip_list or not nested_list:
            return doc, insert_after_paragraph, skip_list
        # Nested list operation starts here    
        parent_text = list_element.get_text().split('\n')[0]
        para_text = l1_prefix + parent_text
        if para_text != '\n':
            insert_after_paragraph, skip_list = self.insert_list_para(list_element, insert_after_paragraph, doc, para_text, skip_list, indent_level = indent_level, prefix = l1_prefix)
            skip_list.append(list_element)
        # Level 2 list
        for l2_idx, nested_list_element in enumerate(nested_list.find_all('li')):
            if nested_list_element.get_text() == '\n':
                continue
            l3_nested_list = nested_list_element.find(['ul', 'ol'], recursive = False)
            if l3_nested_list:
                doc, insert_after_paragraph, skip_list = self.apply_nested_list_formatting(nested_list_element, l3_nested_list, doc, insert_after_paragraph, prefix = '', skip_list = skip_list, indent_level = indent_level + 1, num_list = False)
                skip_list.append(nested_list_element)
            elif nested_list_element not in skip_list and nested_list_element.get_text() != '\n':
                l2_prefix = self.get_prefix(nested_list, l2_idx)
                para_text = nested_list_element.get_text()
                insert_after_paragraph, skip_list = self.insert_list_para(nested_list_element, insert_after_paragraph, doc, para_text, skip_list, indent_level = indent_level + 1, prefix = l2_prefix)
                skip_list.append(nested_list_element)
        
        return doc, insert_after_paragraph, skip_list

    def get_prefix(self, nested_list, sr_no):
        if nested_list.name == 'ol':
            prefix =  f'{roman.toRoman(sr_no + 1).lower()}. '
        else:
            prefix = '- '

        return prefix

    def apply_table_formatting(self, doc, element, insert_after_paragraph):
        # Create a new table
        rows = element.find_all('tr')
        num_rows = len(rows)
        num_cols = len(rows[0].find_all(['td', 'th']))
        table = doc.add_table(rows=num_rows, cols=num_cols)
        table.style = 'Table Grid'
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            for col_idx, cell in enumerate(cells):
                cell_text = cell.get_text()
                table.cell(row_idx, col_idx).text = cell_text
                # Make the header row bold
                if row_idx == 0:
                    table.cell(row_idx, col_idx).paragraphs[0].runs[0].bold = True
                # Adjust font size
                for paragraph in table.cell(row_idx, col_idx).paragraphs:
                    paragraph.alignment = WD_TABLE_ALIGNMENT.LEFT
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
                table.cell(row_idx, col_idx).vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        # Set table borders
        table = self.set_table_borders(table)
        insert_after_paragraph._element.addnext(table._element)
        insert_after_paragraph = table

        return doc, insert_after_paragraph            

    def apply_markdown_formatting(self, doc, markdown_text, insert_after_paragraph):
        """
        Apply markdown formatting to a document.
        """
        # Convert markdown to HTML
        html = markdown2.markdown(markdown_text, extras=["tables"])
        skip_nested = []
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        # Get a list of stylized elements
        stylized_elements = soup.find_all(['strong', 'em', 'code'])
        for element in soup.find_all():
            # Format headers
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                doc, insert_after_paragraph = self.apply_header_formatting(doc, element, insert_after_paragraph)
            # Format paragraphs
            elif element.name in ['p']:
                if element.parent.name == 'li':
                    continue
                doc, insert_after_paragraph = self.apply_para_formatting(doc, element, insert_after_paragraph, stylized_elements)
            # Format lists
            elif element.name in ['ul', 'ol']:
                num_list = True if element.name == 'ol' else False
                if element in skip_nested:
                    continue
                doc, insert_after_paragraph, skip_nested = self.apply_list_formatting(element, doc, insert_after_paragraph, num_list = num_list)
            # Format table
            elif element.name == 'table':
                doc, insert_after_paragraph = self.apply_table_formatting(doc, element, insert_after_paragraph)

        return doc, insert_after_paragraph

    def ensure_styles(self, doc):
        """
        Ensure that the required styles exist in the document.
        """
        self.styles = doc.styles
        # Create List Bullet style if it doesn't exist
        if MISC.DOC_STYLE_LB not in self.styles:
            style = self.styles.add_style(MISC.DOC_STYLE_LB, 1)  # 1 is for paragraph style
            style.font.size = Pt(12)
            style.paragraph_format.left_indent = Pt(18)
            style.paragraph_format.space_after = Pt(6)

        # Create List Number style if it doesn't exist
        if MISC.DOC_STYLE_LN not in self.styles:
            style = self.styles.add_style(MISC.DOC_STYLE_LN, 1)  # 1 is for paragraph style
            style.font.size = Pt(12)
            style.paragraph_format.left_indent = Pt(18)
            style.paragraph_format.space_after = Pt(6)

        # Ensure Table Grid style exists
        if MISC.DOC_STYLE_TB not in self.styles:
            style = self.styles.add_style(MISC.DOC_STYLE_TB, 3)  # 3 is for table style
            style.font.size = Pt(12)

        # Ensure Heading styles exist
        for header_level in range(1, 7):
            heading_style = f'Heading {header_level}'
            if heading_style not in self.styles:
                style = self.styles.add_style(heading_style, 1)  # 1 is for paragraph style
                style.font.size = Pt(12 + (6 - header_level))  # Adjust font size based on heading level
                style.font.bold = True

        return doc

    def add_doc_style(self, run, styles):
        for style in styles:
            if style == 'strong':
                run.bold = True
            if style == 'em':
                run.italic = True
            if style == 'code':
                run.font.name = 'Courier New'

        return run

    def set_table_borders(self, table):
        """
        Set borders for all cells in the table.
        """
        tbl = table._element
        tbl_pr = tbl.tblPr
        tbl_borders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), 'auto')
            tbl_borders.append(border)
        tbl_pr.append(tbl_borders)

        return table

    def change_para_font(self, paragraph):
        for run in paragraph.runs:
            run.font.name = 'Calibri'
        
        return paragraph

    def format_and_replace(self, doc, placeholder, response_text):
        # Ensure doc has styles
        doc = self.ensure_styles(doc)
        # Iterate through all paragraphs in the document
        for paragraph in doc.paragraphs:
            if placeholder in paragraph.text:
                # Split the paragraph text by the target string
                parts = paragraph.text.split(placeholder)
                # Clear the paragraph text
                paragraph.clear()
                # Add the text before the target string
                if parts[0]:
                    paragraph.add_run(parts[0])
                # Add the markdown formatted text
                doc, insert_after_paragraph = self.apply_markdown_formatting(doc, response_text, paragraph)
                
                # Add the text after the target string
                if len(parts) > 1 and parts[1]:
                    new_paragraph = doc.add_paragraph(parts[1])
                    insert_after_paragraph._element.addnext(new_paragraph._element)
            # Make font uniform
            paragraph = self.change_para_font(paragraph)

        return doc