from django.core.management.base import BaseCommand, CommandError
from crawler.models import KnowledgeBase
from crawler.utils import crawl_and_store
from crawler.config import URLS_TO_SCRAPE
import time

class Command(BaseCommand):
    help = 'Crawls specified URLs or predefined URLs and stores them in the KnowledgeBase'
    
    def add_arguments(self, parser):
        parser.add_argument('--urls', nargs='+', type=str, help='Custom URLs to crawl')
        parser.add_argument('--use-config', action='store_true', help='Use URLs from config.py')
        parser.add_argument('--delay', type=int, default=1, help='Delay between requests in seconds (default: 1)')
    
    def handle(self, *args, **options):
        urls = options['urls'] if options['urls'] else None
        use_config = options['use_config']
        delay = options['delay']
        
        # No arguments provided, show help
        if not urls and not use_config:
            self.stdout.write(self.style.WARNING('No URLs specified. Use --urls or --use-config option.'))
            self.stdout.write(self.style.WARNING('Example: python manage.py crawl_urls --use-config'))
            self.stdout.write(self.style.WARNING('Example: python manage.py crawl_urls --urls https://example.com'))
            return
        
        # Use URLs from config
        if use_config:
            urls = URLS_TO_SCRAPE
            self.stdout.write(f'Using {len(urls)} URLs from config')
        
        success_count = 0
        failed_urls = []
        
        for i, url in enumerate(urls, 1):
            self.stdout.write(f'[{i}/{len(urls)}] Crawling {url}...')
            result = crawl_and_store(url, KnowledgeBase)
            
            if result:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully crawled and stored: {url}\n'
                    f'  Title: {result.title}\n'
                    f'  Tags: {result.tags}'
                ))
            else:
                failed_urls.append(url)
                self.stdout.write(self.style.ERROR(f'Failed to crawl {url}'))
            
            # Add delay between requests if not the last URL
            if i < len(urls) and delay > 0:
                self.stdout.write(f'Waiting {delay} seconds before next request...')
                time.sleep(delay)
        
        self.stdout.write(self.style.SUCCESS(
            f'Finished crawling. Success: {success_count}/{len(urls)}'
        ))
        
        if failed_urls:
            self.stdout.write(self.style.WARNING('Failed URLs:'))
            for url in failed_urls:
                self.stdout.write(f'  - {url}')
