'use client'

export const Footer = () => {
  return (
    <footer className="border-t border-dark-border bg-dark-surface/50 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🎬</span>
              <span className="font-bold">
                <span className="text-gradient">ClipPilot</span> Lite
              </span>
            </div>
            <p className="text-gray-400 text-sm">
              AI-powered short video generation for everyone.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold mb-3">Product</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#features" className="hover:text-white transition-colors">
                  Features
                </a>
              </li>
              <li>
                <a href="/create" className="hover:text-white transition-colors">
                  Create
                </a>
              </li>
              <li>
                <a href="/dashboard" className="hover:text-white transition-colors">
                  Dashboard
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold mb-3">Legal</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-dark-border py-8">
          {/* AI Disclaimer */}
          <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm text-yellow-400">
            <p className="font-semibold mb-2">⚠️ AI-Generated Content Disclaimer</p>
            <p>
              ClipPilot Lite uses artificial intelligence to research topics,
              write scripts, generate narration, and create videos. While we
              strive for accuracy, please review all generated content before
              sharing publicly. AI-generated content may contain inaccuracies or
              may require fact-checking.
            </p>
          </div>

          {/* Copyright */}
          <div className="text-center text-sm text-gray-500">
            <p>
              © {new Date().getFullYear()} ClipPilot Lite. All rights reserved.
            </p>
            <p className="mt-2">
              Built with AI technology. Designed for content creators.
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
