# Family Tree Frontend - React Application

A modern React frontend for the Family Tree application with interactive visualization, user management, and real-time updates.

## 🎯 Features

### ✅ **Implemented**
- **User Authentication** - Register, login, logout with JWT token management
- **Dashboard Management** - View, create, and delete family trees
- **Interactive Family Trees** - React Flow visualization with draggable person cards
- **Person Management** - Add, view, edit, and delete family members
- **Real-time Updates** - Automatic UI refresh without page reloads
- **Responsive Design** - Works seamlessly on desktop and mobile
- **Form Validation** - Comprehensive client-side validation with error handling
- **Modern UI/UX** - Clean, intuitive interface with Tailwind CSS
- **Navigation** - Seamless routing between pages and features
- **Error Handling** - User-friendly error messages and loading states

### 🚧 **Ready for Implementation**
- **Relationship Creation** - UI for connecting family members
- **File Upload** - Photo and document management for people
- **Advanced Visualization** - Enhanced family tree layouts and styling
- **Search & Filter** - Find people within large family trees
- **Export Features** - Print and save family tree data

## 🛠 Technology Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type safety and better development experience
- **React Router** - Client-side routing and navigation
- **TanStack Query** - Powerful data fetching and state management
- **React Hook Form** - Efficient form handling with validation
- **Tailwind CSS** - Utility-first CSS framework for rapid styling
- **React Flow** - Interactive node-based family tree visualization
- **Axios** - HTTP client for API communication

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html                 # Main HTML template
├── src/
│   ├── components/                # Reusable UI components
│   │   ├── FamilyTree/           # Family tree specific components
│   │   │   ├── CreateFamilyTreeModal.tsx
│   │   │   ├── FamilyTreeVisualization.tsx  # React Flow integration
│   │   │   └── PersonNode.tsx     # Individual person cards
│   │   ├── Layout/               # Layout components
│   │   │   └── Navbar.tsx        # Navigation bar
│   │   ├── Person/               # Person management
│   │   │   └── AddPersonModal.tsx
│   │   └── UI/                   # Generic UI components
│   │       └── LoadingSpinner.tsx
│   ├── contexts/                 # React context providers
│   │   └── AuthContext.tsx       # Authentication state management
│   ├── pages/                    # Main page components
│   │   ├── DashboardPage.tsx     # Family trees overview
│   │   ├── FamilyTreePage.tsx    # Interactive family tree view
│   │   ├── LoginPage.tsx         # User authentication
│   │   ├── PersonPage.tsx        # Individual person details
│   │   └── RegisterPage.tsx      # User registration
│   ├── services/                 # API integration
│   │   └── api.ts                # Backend API client
│   ├── App.tsx                   # Main application component
│   ├── index.tsx                 # Application entry point
│   └── index.css                 # Global styles and Tailwind imports
├── package.json                  # Dependencies and scripts
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm start
```

The application will open at http://localhost:3000 and automatically proxy API requests to the backend.

### 3. Build for Production
```bash
npm run build
```

## 📱 Application Flow

### 1. **Authentication**
- Users can register new accounts or login to existing ones
- JWT tokens are stored in localStorage and automatically included in API requests
- Protected routes redirect to login if not authenticated

### 2. **Dashboard**
- Overview of all user's family trees
- Create new family trees with name and description
- Delete existing family trees with confirmation
- Navigate to individual family tree views

### 3. **Family Tree Visualization**
- Interactive React Flow canvas with person cards
- Add new people with comprehensive biographical information
- Delete people with confirmation dialogs
- Navigate to detailed person pages
- Real-time updates when data changes

### 4. **Person Management**
- Detailed person pages with biographical information
- Support for birth/death dates, places, biography
- File attachment placeholders (ready for implementation)
- Edit and update person information

## 🎨 UI/UX Features

### **Modern Design**
- Clean, minimalist interface with thoughtful spacing
- Consistent color scheme with primary blue theme
- Hover effects and smooth transitions
- Mobile-responsive layout that works on all devices

### **Interactive Elements**
- Draggable person cards in family tree visualization
- Modal dialogs for forms and confirmations
- Loading spinners and skeleton states
- Error boundaries and graceful error handling

### **Accessibility**
- Semantic HTML structure
- Proper ARIA labels and roles
- Keyboard navigation support
- High contrast ratios for readability

## 🔧 Technical Implementation

### **State Management**
- **TanStack Query** for server state management with caching
- **React Context** for global authentication state
- **React Hook Form** for form state and validation
- **Local state** with useState for component-specific data

### **API Integration**
- Centralized API client with Axios
- Automatic JWT token inclusion in requests
- Response caching and background refetching
- Error handling with user-friendly messages

### **Routing**
- Protected routes that require authentication
- Public routes for login/register
- Programmatic navigation with React Router
- Clean URL structure for bookmarking

### **Form Handling**
- Client-side validation with React Hook Form
- Real-time validation feedback
- Proper error message display
- Optimistic updates where appropriate

## 📊 Data Flow

### **Authentication Flow**
1. User submits login/register form
2. API request sent to backend
3. JWT token received and stored in localStorage
4. User redirected to dashboard
5. All subsequent requests include Authorization header

### **Family Tree Flow**
1. Dashboard loads user's family trees
2. User creates new family tree or selects existing one
3. Family tree page loads graph data from API
4. React Flow renders interactive visualization
5. User interactions trigger API calls and UI updates

### **Person Management Flow**
1. User adds person through modal form
2. Form data validated and sent to API
3. Success triggers query invalidation
4. UI automatically updates with new person
5. Delete operations follow similar pattern with confirmation

## 🎯 React Flow Integration

### **Custom Node Types**
- **PersonNode** - Custom React component for person cards
- Displays name, dates, places, and photo placeholder
- Interactive buttons for edit and delete actions
- Responsive design that works at different zoom levels

### **Graph Layout**
- Automatic positioning for new nodes
- Grid-based layout for consistent spacing
- Support for dragging and repositioning
- Smooth animations and transitions

### **Interactive Features**
- Click person cards to navigate to detail pages
- Delete confirmation dialogs
- Hover effects for better user feedback
- Zoom and pan controls for large family trees

## 🔒 Security Features

- **JWT Token Management** - Automatic token inclusion and expiration handling
- **Protected Routes** - Authentication required for app features
- **Input Validation** - Client-side validation prevents invalid data submission
- **XSS Protection** - Proper data sanitization and encoding
- **CORS Configuration** - Proper cross-origin request handling

## 📱 Responsive Design

### **Breakpoints**
- **Mobile** (< 768px) - Single column layout, touch-optimized
- **Tablet** (768px - 1024px) - Adapted layouts with sidebar
- **Desktop** (> 1024px) - Full multi-column experience

### **Mobile Optimizations**
- Touch-friendly button sizes and spacing
- Collapsible navigation menu
- Optimized form layouts for small screens
- Finger-friendly interaction targets

## 🧪 Development Tools

### **Available Scripts**
```bash
npm start          # Development server with hot reload
npm run build      # Production build
npm test           # Run test suite (when implemented)
npm run eject      # Eject from Create React App (not recommended)
```

### **Code Quality**
- TypeScript for type safety
- ESLint for code quality
- Prettier for code formatting (when configured)
- React DevTools for debugging

## 🚀 Production Deployment

### **Build Optimization**
- Tree shaking for smaller bundle sizes
- Code splitting with React.lazy
- Asset optimization and compression
- Service worker for offline capability (configurable)

### **Environment Variables**
```bash
REACT_APP_API_URL=https://api.yourdomain.com  # Backend API URL
```

### **Deployment Options**
- **Static hosting** - Netlify, Vercel, GitHub Pages
- **CDN deployment** - AWS CloudFront, Azure CDN
- **Docker containers** - Nginx-based container
- **Traditional web servers** - Apache, Nginx

## 🔄 Recent Updates

- **Fixed React Flow updates** - Real-time visualization updates without page refresh
- **Enhanced error handling** - Better user feedback for API errors
- **Improved form validation** - Comprehensive client-side validation
- **Delete functionality** - Complete person deletion with confirmation
- **Mobile responsiveness** - Optimized for all device sizes
- **Performance optimizations** - Reduced re-renders and improved caching

## 🎯 Next Steps

### **High Priority**
1. **Relationship Creation** - UI for connecting family members
2. **File Upload** - Photo and document management
3. **Person Editing** - In-place editing of person details
4. **Search Functionality** - Find people within family trees

### **Medium Priority**
1. **Advanced Layouts** - Better automatic positioning algorithms
2. **Export Features** - PDF generation and data export
3. **Bulk Operations** - Select and operate on multiple people
4. **Undo/Redo** - Action history and reversal

### **Low Priority**
1. **Themes** - Dark mode and custom color schemes
2. **Animations** - Enhanced transitions and micro-interactions
3. **Offline Support** - Local storage and sync capabilities
4. **Collaboration** - Real-time collaborative editing

## 🐛 Known Issues

- **VS Code Import Warnings** - Some TypeScript import warnings that don't affect functionality
- **Auth Flow Edge Cases** - Occasional need to refresh after registration
- **React Flow Performance** - Large family trees (100+ people) may need optimization

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new components
3. Add proper error handling and loading states
4. Test on multiple browsers and devices
5. Update documentation for new features

## 📝 Dependencies

### **Core Dependencies**
- React 18.2.0 - UI framework
- TypeScript 4.9.5 - Type safety
- React Router 6.20.1 - Routing
- TanStack Query 5.17.0 - Data fetching
- React Hook Form 7.48.2 - Form handling
- Tailwind CSS 3.3.6 - Styling
- React Flow 11.10.1 - Graph visualization
- Axios 1.6.2 - HTTP client

### **Development Dependencies**
- @types packages for TypeScript support
- Tailwind plugins for enhanced functionality
- PostCSS for CSS processing
- Autoprefixer for browser compatibility

This frontend provides a solid foundation for a modern family tree application with room for extensive customization and feature additions.