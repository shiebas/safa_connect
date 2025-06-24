"""
Management command to test document watermarking functionality
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.watermark_utils import create_watermarked_document
from accounts.models import DocumentAccessLog
import os
import tempfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

User = get_user_model()

class Command(BaseCommand):
    help = 'Test document watermarking functionality'
    
    def add_arguments(self, parser):
        parser.add_argument('--user-email', type=str, help='Email of user to test with')
        parser.add_argument('--test-file', type=str, help='Path to test file')
    
    def handle(self, *args, **options):
        # Get or create test user
        user_email = options.get('user_email', 'test@safa.co.za')
        try:
            user = User.objects.get(email=user_email)
            self.stdout.write(f"Using user: {user.get_full_name()} ({user.email})")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email {user_email} not found"))
            return
        
        # Create test PDF if no file provided
        test_file = options.get('test_file')
        if not test_file:
            test_file = self.create_test_pdf()
            self.stdout.write(f"Created test PDF: {test_file}")
        
        if not os.path.exists(test_file):
            self.stdout.write(self.style.ERROR(f"Test file not found: {test_file}"))
            return
        
        # Test watermarking
        self.stdout.write("Testing document watermarking...")
        
        watermarked_path = create_watermarked_document(
            user, 
            test_file, 
            f"Test Document - {os.path.basename(test_file)}"
        )
        
        if watermarked_path:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Watermarking successful! Output: {watermarked_path}")
            )
            
            # Test file size comparison
            original_size = os.path.getsize(test_file)
            watermarked_size = os.path.getsize(watermarked_path)
            
            self.stdout.write(f"Original size: {original_size} bytes")
            self.stdout.write(f"Watermarked size: {watermarked_size} bytes")
            self.stdout.write(f"Size difference: {watermarked_size - original_size} bytes")
            
            # Create test access log
            DocumentAccessLog.objects.create(
                user=user,
                document_name=os.path.basename(test_file),
                document_type='test_document',
                document_owner='Test System',
                action='download',
                ip_address='127.0.0.1',
                user_agent='Test Command',
                file_size=watermarked_size,
                watermarked=True,
                success=True,
                notes='Test watermarking via management command'
            )
            
            self.stdout.write("✅ Test access log created")
            
            # Clean up temporary watermarked file
            try:
                os.unlink(watermarked_path)
                self.stdout.write("🧹 Cleaned up temporary watermarked file")
            except:
                pass
                
        else:
            self.stdout.write(self.style.ERROR("❌ Watermarking failed"))
        
        # Clean up test file if we created it
        if not options.get('test_file'):
            try:
                os.unlink(test_file)
                self.stdout.write("🧹 Cleaned up test file")
            except:
                pass
        
        # Show recent access logs
        recent_logs = DocumentAccessLog.objects.filter(user=user).order_by('-access_time')[:5]
        
        self.stdout.write("\n📊 Recent document access logs:")
        for log in recent_logs:
            watermark_status = "🛡️ Watermarked" if log.watermarked else "⚠️ Not watermarked"
            success_status = "✅ Success" if log.success else "❌ Failed"
            
            self.stdout.write(
                f"  {log.access_time.strftime('%Y-%m-%d %H:%M')} - "
                f"{log.document_name} - {log.action} - "
                f"{watermark_status} - {success_status}"
            )
    
    def create_test_pdf(self):
        """Create a simple test PDF"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            
            # Add some content
            c.setFont("Helvetica", 16)
            c.drawString(100, 750, "SAFA Test Document")
            c.setFont("Helvetica", 12)
            c.drawString(100, 720, "This is a test document for watermarking functionality.")
            c.drawString(100, 700, "It contains sample content to verify that watermarking")
            c.drawString(100, 680, "works correctly with PDF documents.")
            
            # Add some more content
            for i in range(10):
                y = 650 - (i * 20)
                c.drawString(100, y, f"Sample line {i+1} - Lorem ipsum dolor sit amet")
            
            c.save()
            return temp_file.name
