#!/bin/bash

# PathoScope Development Setup Script
# This script sets up the development environment for PathoScope

set -e

echo "🏥 Setting up PathoScope Hospital Infection Control System..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment files if they don't exist
echo "📝 Setting up environment files..."

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from example"
else
    echo "ℹ️  backend/.env already exists"
fi

if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "✅ Created frontend/.env.local from example"
else
    echo "ℹ️  frontend/.env.local already exists"
fi

# Build and start the services
echo "🐳 Building and starting Docker services..."

# Build the services
docker-compose build

# Start the database and redis first
echo "🗄️  Starting database services..."
docker-compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check if database is ready
until docker-compose exec postgres pg_isready -U pathoscope -d pathoscope_db; do
    echo "Waiting for postgres..."
    sleep 2
done

echo "✅ Database is ready!"

# Start the backend
echo "🔧 Starting backend service..."
docker-compose up -d backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 15

# Check if backend is ready
until curl -f http://localhost:8000/health &> /dev/null; do
    echo "Waiting for backend..."
    sleep 2
done

echo "✅ Backend is ready!"

# Start the frontend
echo "🎨 Starting frontend service..."
docker-compose up -d frontend

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
sleep 15

# Check if frontend is ready
until curl -f http://localhost:3000 &> /dev/null; do
    echo "Waiting for frontend..."
    sleep 2
done

echo "✅ Frontend is ready!"

# Show the URLs
echo ""
echo "🎉 PathoScope is now running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/docs"
echo ""
echo "📋 Default Login (after creating a user in the system):"
echo "   Email: admin@pathoscope.hospital"
echo "   Password: (set during user creation)"
echo ""
echo "🛠️  Development Commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo ""
echo "📚 For more information, see the README.md file."
echo ""
echo "Happy infection tracking! 🦠"