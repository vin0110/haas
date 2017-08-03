def create_stack(name, key, body, mclient):
    '''creates a stack'''
    parameters = dict(KeyName=key, )
    parameter_list = [
        dict(ParameterKey=param, ParameterValue=parameters[param])
        for param, value in parameters.items()]
    mclient.create_stack(StackName=name,
                         TemplateBody=body,
                         Parameters=parameter_list,
                         Capabilities=['CAPABILITY_IAM'])
