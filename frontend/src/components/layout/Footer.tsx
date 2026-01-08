export default function Footer() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 mt-auto">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            © {new Date().getFullYear()} Ghostwriter Forensic Analytics. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
            <a href="#" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
              Privacy
            </a>
            <a href="#" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
              Terms
            </a>
            <a href="#" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
              Support
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
