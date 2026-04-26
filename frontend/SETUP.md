# ClipPilot Lite Frontend - Setup Guide

Complete setup instructions for developing and running the ClipPilot Lite frontend.

## Prerequisites

- **Node.js**: 18.x or higher (check with `node --version`)
- **npm**: 9.x or higher (usually comes with Node.js)
- **Git**: For cloning and version control
- **Supabase Account**: For authentication (free tier available)
- **Backend Running**: ClipPilot backend must be accessible

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.local.example .env.local

# Edit with your actual values
# Use your editor of choice (nano, vim, VS Code, etc.)
nano .env.local
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Detailed Setup

### Step 1: Verify Prerequisites

```bash
# Check Node.js version (should be 18+)
node --version

# Check npm version (should be 9+)
npm --version

# Check git
git --version
```

### Step 2: Clone Repository

```bash
# If you haven't already cloned it
git clone https://github.com/yourusername/clippilot.git
cd clippilot/frontend
```

### Step 3: Supabase Setup

1. **Create Supabase Project** (if you haven't):
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Wait for project to initialize (1-2 minutes)

2. **Get Credentials**:
   - Go to project Settings > API
   - Copy `URL` and `anon public key`
   - These go in `.env.local` as:
     ```
     NEXT_PUBLIC_SUPABASE_URL=<URL>
     NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key>
     ```

3. **Setup Authentication**:
   - Go to Authentication > Providers
   - Ensure "Email" is enabled
   - Go to URL Configuration
   - Add your site URLs:
     - Redirect URL: `http://localhost:3000/auth/callback`
     - (For production: `https://yourdomain.com/auth/callback`)

### Step 4: Backend Configuration

1. **Get Backend URL**:
   - If running locally: `http://localhost:8000`
   - If deployed: `https://your-api-domain.com`

2. **Add to `.env.local`**:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Verify Backend is Running**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return a successful response.

### Step 5: Install Node Dependencies

```bash
npm install
```

This installs all required packages listed in `package.json`:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Supabase client libraries

### Step 6: Run Development Server

```bash
npm run dev
```

Expected output:
```
  ▲ Next.js 14.0.0
  - Local:        http://localhost:3000
  - Environments: .env.local
  ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Step 7: Verify Installation

1. Open browser to [http://localhost:3000](http://localhost:3000)
2. You should see the ClipPilot Lite landing page
3. Click "Get Started Free"
4. You should be redirected to `/auth`
5. Try creating an account with test email

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://abc123.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJhbGc...` |
| `NEXT_PUBLIC_API_URL` | Backend API endpoint | `http://localhost:8000` |

### Important Notes

- All `NEXT_PUBLIC_*` variables are exposed to the browser
- Never commit `.env.local` to git
- Use `.env.local.example` as a template
- Different values for dev/staging/production

### Create `.env.local` File

```bash
# Manual creation
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

## Development Workflow

### Common Commands

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Run production build locally
npm run start

# Check TypeScript types
npm run type-check

# Run ESLint
npm run lint

# Update dependencies
npm update
```

### File Structure for Development

```
src/
├── app/              # Next.js pages (routes)
│   └── page.tsx      # Edit to modify pages
├── components/       # Reusable components
│   └── Navbar.tsx    # Edit to modify components
├── lib/              # Utilities and helpers
│   ├── api.ts        # API client functions
│   └── hooks.ts      # Custom React hooks
└── styles/           # Global styles
    └── globals.css   # Edit for design changes
```

### Adding a New Page

1. Create file in `src/app/newpage/page.tsx`:
   ```typescript
   export default function NewPage() {
     return (
       <div className="container mx-auto py-8">
         <h1>My New Page</h1>
       </div>
     )
   }
   ```

2. Access at `/newpage`

### Styling with Tailwind

All styling uses Tailwind CSS classes:

```tsx
<div className="bg-dark-surface border border-dark-border rounded-lg p-6">
  <h1 className="text-2xl font-bold text-gradient mb-4">
    Hello World
  </h1>
  <p className="text-gray-400">This uses Tailwind classes</p>
</div>
```

Custom colors defined in `tailwind.config.ts`:
- `primary-*` (indigo/violet)
- `secondary-*` (purple)
- `dark-*` (dark theme colors)

## Debugging

### Browser DevTools

1. Open browser DevTools (F12 or Cmd+Option+I on Mac)
2. Check Console tab for errors
3. Use Network tab to inspect API calls
4. Use Application tab to see LocalStorage/Cookies

### Next.js Debug Mode

```bash
# Run with debug logging
NODE_DEBUG=* npm run dev
```

### TypeScript Errors

```bash
# Find type errors
npm run type-check

# Watch mode
npx tsc --watch --noEmit
```

### API Debugging

Check what's being sent to the backend:

1. Open DevTools > Network tab
2. Filter by "Fetch/XHR"
3. Click on API request
4. See Request/Response headers and body

### Common Issues

#### "Cannot find module '@/...'"

Path aliases not working. Check `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

#### Videos not loading from Supabase

1. Check storage bucket exists
2. Verify bucket is public
3. Check image domains in `next.config.js`

#### Port 3000 already in use

```bash
# Find and kill process using port 3000
# macOS/Linux
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

#### "CORS error" from API

1. Verify backend CORS is enabled
2. Check `NEXT_PUBLIC_API_URL` is correct
3. Ensure backend is running and accessible

## Testing

### Manual Testing Checklist

- [ ] Landing page loads without errors
- [ ] Can navigate to auth page
- [ ] Can sign up with email/password
- [ ] Can sign in to account
- [ ] Videos remaining counter shows
- [ ] Can create video (with test topic)
- [ ] Status page shows progress
- [ ] Can view completed video
- [ ] Can download video
- [ ] Can view dashboard
- [ ] Sign out works

### Testing with Different Browsers

```bash
# Install dev tools
npm install --save-dev @testing-library/react @testing-library/jest-dom

# Run tests (when configured)
npm test
```

## Performance Optimization

### Check Bundle Size

```bash
npm install --save-dev @next/bundle-analyzer

# Add to next.config.js:
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

export default withBundleAnalyzer({
  // your config
})

# Run analysis
ANALYZE=true npm run build
```

### Lighthouse Audit

1. Open DevTools
2. Go to Lighthouse tab
3. Click "Generate report"
4. Review suggestions

## Deployment Preparation

### Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] TypeScript types check: `npm run type-check`
- [ ] No console errors or warnings
- [ ] Test on different browsers
- [ ] Mobile responsive testing
- [ ] Performance acceptable (Lighthouse score 80+)
- [ ] Security headers configured (via backend)

### Build for Production

```bash
# Clean build
rm -rf .next
npm run build

# Test production build
npm start

# Open http://localhost:3000
```

### Deploy to Vercel

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed Vercel instructions.

## Updating Dependencies

```bash
# Check for outdated packages
npm outdated

# Update all packages to latest minor version
npm update

# Update to latest major version (be careful)
npm install [package]@latest

# Check for security issues
npm audit

# Fix security issues automatically
npm audit fix
```

## IDE Setup

### VS Code (Recommended)

Install extensions:
- **ES7+ React/Redux/React-Native snippets** (dsznajder.es7-react-js-snippets)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
- **TypeScript Vue Plugin** (Vue.vscode-typescript-vue-plugin)
- **Prettier** (esbenp.prettier-vscode)
- **ESLint** (dbaeumer.vscode-eslint)

### Settings

Create `.vscode/settings.json`:
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Getting Help

### Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

### Debugging Tips

1. **Read error messages carefully** - they often tell you exactly what's wrong
2. **Check browser console** for JavaScript errors
3. **Use DevTools Network tab** to inspect API calls
4. **Check backend logs** if API calls fail
5. **Search GitHub Issues** for your problem
6. **Post in discussions** with error message and reproduction steps

## Next Steps

1. Complete the setup guide for the backend: `../backend/SETUP.md`
2. Read the [README.md](./README.md) for architecture overview
3. Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment options
4. Review [package.json](./package.json) to understand dependencies
5. Start developing!

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Port 3000 in use | Kill process: `lsof -ti:3000 \| xargs kill -9` |
| Module not found | Clear cache: `rm -rf node_modules package-lock.json && npm install` |
| TypeScript errors | Run: `npm run type-check` |
| Styles not loading | Restart dev server and hard refresh browser (Ctrl+Shift+R) |
| API 404 errors | Verify backend is running and URL is correct |
| CORS errors | Check backend CORS config for your frontend URL |
| Supabase auth fails | Verify credentials in .env.local |
| Video not playing | Check storage bucket and image domain config |

## Support

For issues:
1. Check this guide and README
2. Search GitHub issues
3. Check backend status and logs
4. Post detailed error message with context

Happy coding!
