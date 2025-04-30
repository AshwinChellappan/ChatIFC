from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import html
from dotenv import load_dotenv
import os
from core.config import settings
from azure.ai.documentintelligence import DocumentIntelligenceClient

class ExtractTableService:

    def __init__(self):
        self.adi_endpoint = settings.AZURE_ADI_ENDPOINT
        self.adi_credential = AzureKeyCredential(settings.AZURE_ADI_KEY)

    def table_to_html(self,table):
        table_html = "<table>"
        rows = [sorted([cell for cell in table.cells if cell.row_index == i],
                    key=lambda cell: cell.column_index) for i in range(table.row_count)]
        for row_cells in rows:
            table_html += "<tr>"
            for cell in row_cells:
                tag = "th" if (
                    cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
                cell_spans = ""
                if cell.column_span > 1:
                    cell_spans += f" colSpan={cell.column_span}"
                if cell.row_span > 1:
                    cell_spans += f" rowSpan={cell.row_span}"
                table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html

    def extract_with_custom_overlap(self,content, table_start, table_end, total_length, chunk_size, chunk_overlap):
        # Calculate the chunk size and overlap
        before_start = max(0, table_start - chunk_size + chunk_overlap)
        after_end = min(total_length, table_end + chunk_size - chunk_overlap)
        
        return content[before_start:table_start], content[table_start:table_end], content[table_end:after_end]

    def recognize_tables(self,blob_data,chunkSize,chunkOverlap):

        # Set up the Document Analysis client
        document_analysis_client = DocumentAnalysisClient(
            self.adi_endpoint, self.adi_credential, headers={
                "x-ms-useragent": "azure-search-chat-demo/1.0.0"})

        tables_with_context = []

        # Start the recognition process using the blob data
        poller = document_analysis_client.begin_analyze_document(
            model_id="prebuilt-layout", document=blob_data)

        # Get the result
        form_recognizer_results = poller.result()

        # Extracted data from the result
        for page_num, page in enumerate(form_recognizer_results.pages):
            tables_on_page = [table for table in form_recognizer_results.tables 
                            if table.bounding_regions[0].page_number == page_num + 1]

            # Mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            total_page_content = form_recognizer_results.content[page_offset:page_offset + page_length]
            
            for table in tables_on_page:
                table_start = table.spans[0].offset - page_offset
                table_end = table_start + table.spans[0].length

                # Use custom chunk and overlap sizes from config
                before, table_content, after = self.extract_with_custom_overlap(
                    total_page_content, table_start, table_end, page_length, 
                    chunk_size=0, chunk_overlap=chunkOverlap)
                
                # Convert table to HTML
                table_html = self.table_to_html(table)
                
                # Combine the table HTML with the context
                table_with_context = before + table_html + after
                tables_with_context.append(table_with_context)

        return tables_with_context

    def extract_ppte_content(self,blob_data):
        # Extract PPTE content
        document_intelligence_client = DocumentIntelligenceClient(endpoint=self.adi_endpoint, credential=self.adi_credential)
        poller = document_intelligence_client.begin_analyze_document("prebuilt-layout", analyze_request=blob_data, content_type="application/pdf")
        texts = poller.result()
        return texts.content

    def extract_all_content(self, blob_data):
        document_analysis_client = DocumentAnalysisClient(
            self.adi_endpoint, self.adi_credential, headers={
                "x-ms-useragent": "azure-search-chat-demo/1.0.0"})
 
        poller = document_analysis_client.begin_analyze_document(
            model_id="prebuilt-layout", document=blob_data)
 
        return poller.result()
   
    # def extract_texts(self, blob_data):
    #     """Extracts text content from the document, omitting table contents."""
    #     texts = []
    #     form_recognizer_results = self.extract_all_content(blob_data)
 
    #     # Collect spans from all cells in detected tables
    #     table_spans = []
    #     for table in form_recognizer_results.tables:
    #         for cell in table.cells:
    #             if cell.spans:  # Ensure spans exist
    #                 table_spans.append((cell.spans[0].offset, cell.spans[0].length))
 
    #     # Extract text from all pages, omitting table contents
    #     for page in form_recognizer_results.pages:
    #         for line in page.lines:
    #             if line.spans:  # Ensure spans exist
    #                 # Check if the line is within any of the table spans
    #                 if not any(start <= line.spans[0].offset < start + length for start, length in table_spans):
    #                     texts.append(html.escape(line.content))
       
    #     return " ".join(texts)

    def extract_texts(self, blob_data):
        """Extracts text content from the document, omitting table contents."""
        texts = []
        form_recognizer_results = self.extract_all_content(blob_data)
        
        table_spans = self.collect_table_spans(form_recognizer_results.tables)
        texts = self.extract_page_texts(form_recognizer_results.pages, table_spans)

        return " ".join(texts)

    def collect_table_spans(self, tables):
        """Collect spans from all cells in detected tables."""
        table_spans = []
        for table in tables:
            for cell in table.cells:
                if cell.spans:
                    table_spans.append((cell.spans[0].offset, cell.spans[0].length))
        return table_spans

    def extract_page_texts(self, pages, table_spans):
        """Extract text from all pages, omitting table contents."""
        texts = []
        for page in pages:
            for line in page.lines:
                if line.spans and not self.is_in_table_spans(line.spans[0], table_spans):
                    texts.append(html.escape(line.content))
        return texts

    def is_in_table_spans(self, line_span, table_spans):
        """Check if the line span is within any of the table spans."""
        return any(start <= line_span.offset < start + length for start, length in table_spans)