# 🚀 Deployment Overview

This project includes comprehensive deployment options for different environments and use cases.

## 🎯 **Quick Start**

Run the main deployment script from the project root:

```bash
./deploy.sh
```

This will present you with deployment options and guide you through the process.

## 📁 **Deployment Organization**

All deployment files are organized in the `deployment/` directory:

- **`deployment/dev/`** - Development environment (EC2, HTTP, debug mode)
- **`deployment/prod/`** - Production environment (EC2, HTTPS, monitoring)
- **`deployment/lambda/`** - AWS Lambda & SQS setup
- **`deployment/guides/`** - Documentation and guides

## 🚀 **Deployment Paths**

### **1. Development First (Recommended)**
```bash
cd deployment/dev
./deploy_dev.sh
```

### **2. Production Ready**
```bash
cd deployment/prod
./deploy_ec2.sh
```

### **3. Add Scaling**
```bash
cd deployment/lambda
./deploy_lambda.sh
```

## 📚 **Documentation**

- **Main Guide**: `deployment/README.md`
- **Quick Start**: `deployment/guides/REMOTE_DEV_QUICKSTART.md`
- **Production**: `deployment/guides/EC2_DEPLOYMENT_GUIDE.md`
- **Lambda**: `deployment/guides/SQS_LAMBDA_ARCHITECTURE.md`

## 🎯 **Choose Your Path**

- **🧪 Development**: Start here for testing ($11-20/month)
- **🚀 Production**: Live application with SSL ($21-60/month)
- **⚡ Lambda**: Add async processing ($5-20/month)

---

**🚀 Ready to deploy? Run `./deploy.sh` to get started!**
