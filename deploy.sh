
# Install the required custom resources by running the command: knative-v1.16.0
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.9.1/serving-crds.yaml

# Install the core components of Knative Serving by running the command:
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.9.1/serving-core.yaml

# Install the Knative Kourier controller by running the command: 
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.9.1/kourier.yaml

# Configure Knative Serving to use Kourier by default by running the command: 
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
 
# Configure DNS
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.9.1/serving-default-domain.yaml

kubectl patch configmap/config-domain \
  -n knative-serving \
  --type merge \
  -p '{"data":{"127.0.0.1.sslip.io":""}}'


sleep 80

cd cnn_serving
kubectl apply -f cnn_serving.yaml

cd ../img_res
kubectl apply -f img_res.yaml

cd ../img_rot
kubectl apply -f img_rot.yaml

cd ../ml_train
kubectl apply -f ml_train.yaml

cd ../vid_proc
kubectl apply -f vid_proc.yaml

cd ../web_serve
kubectl apply -f web_serve.yaml

cd ..

sleep 30

# python3 knative-all.py
python3 poisonv2.py

# minikube stop
minikube stop