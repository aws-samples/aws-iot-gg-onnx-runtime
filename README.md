
# Optimizing Image Classification on AWS IoT Greengrass using ONNX Runtime

This repository contains the necessary files for building and deploying a custom AWS IoT Greengrass component for image classification.

### Prerequisites
To be able to run through the steps in this blog post, you will need: 

 - 	Basic knowledge of AWS IoT Core and AWS IoT Greengrass 
 - Basic understanding of machine learning concepts 	
 - An AWS Account and an AWS Identity and Access Management (IAM) user with the necessary permissions to create and manage AWS resources
   permissions for creating and managing AWS resources
 - AWS Command Line Interface (AWS CLI) and Git installed	


### Initial Setup
As part of the initial setup for the environment, there are several resources that we need to provision. Follow the steps below to get started:
1.	The component’s artifacts are going to be stored in an Amazon Simple Storage Service (Amazon S3) bucket. 
To create an Amazon S3 bucket, follow the instructions from the [user guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/creating-bucket.html). 
2.	To emulate a device where we will deploy the component, we will use an AWS Cloud9 environment and then install AWS IoT Greengrass client software. 
To perform these steps, follow the instructions from the [AWS IoT Greengrass v2](https://catalog.us-east-1.prod.workshops.aws/workshops/5ecc2416-f956-4273-b729-d0d30556013f/en-US) workshop, sections 2 and 3.1

### Build and Publish the ONNX Runtime and Inference Components
To upload the artifacts to the Amazon S3 bucket created as part of the initial setup, follow the next steps: 
1.	Clone the git repository that contains the component’s artifacts and recipe
git clone https://github.com/aws-samples/aws-iot-gg-onnx-runtime 
2.	Navigate to the artifacts folder and zip the files

    cd artifacts/com.demo.onnx-imageclassification/1.0.0
    zip -r greengrass-onnx.zip .

3.	Upload the zip file to the Amazon S3 bucket that you created in the initial setup.

    aws s3 cp greengrass-onnx.zip s3://{YOUR-S3-BUCKET}/greengrass-onnx.zip

To publish the components, perform the following steps: 
1.	Navigate to the /recipes folder and edit the file com.demo.onnx-imageclassification-1.0.0.json
2.	Replace the Amazon S3 bucket name in artifacts URI with your own bucket name defined above

    "Artifacts": [
            {
              "URI": "s3://{YOUR-S3-BUCKET}/greengrass-onnx.zip",
              "Unarchive": "ZIP"
            }
          ]

3.	Publish the ONNX Runtime component.

    aws greengrassv2 create-component-version --inline-recipe fileb://com.demo.onnxruntime-1.0.0.json

4.	Publish the component that will perform the image classification and that has a dependency on the ONNX Runtime.

    aws greengrassv2 create-component-version --inline-recipe fileb://com.demo.onnx-imageclassification-1.0.0.json

5.	To verify that the components were published successfully, navigate to AWS IoT Console , go to Greengrass Devices >> Components. In My Components tab, you should see the two components that you just published.
### Deploy the component to a target device
1.	To deploy the component to a target device, make sure that you have provisioned an AWS Cloud9 environment with AWS IoT Greengrass client software installed. 
2.	To setup the necessary permissions for the Greengrass device, make sure that the service role associated with the Greengrass device has permissions to retrieve objects from the Amazon S3 bucket you previously created as well as permissions to publish to the AWS IoT topic demo/onnx
3.	To deploy the component to the target device, go to the AWS IoT Console, navigate to Greengrass Devices > Deployments and click on Create.
4.	Fill in the deployment name as well as the name of the core device you want to deploy to.
5.	In the Select Components section, select the component com.demo.onnx-imageclassification 
6.	Leave all other options as default and click Next until you reach the Review section of your deployment and then click Deploy

### Test the ONNX Image Classification Component deployment 
Once the component has been successfully deployed, the ONNX runtime will be installed on the core device, as well as the image classification component. Once the image classification component is running, it will loop through the files in the images folder and it will classify them. The results will be published to AWS IoT Core to the topic demo/onnx. 
To test that the results have been published successfully to the topic, go to AWS IoT Console, navigate to MQTT Client section and Subscribe to the topic demo/onnx.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

