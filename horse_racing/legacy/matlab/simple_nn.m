data = csvread('/Users/ShivaKeihaninejad/Documents/horse-riding/horse_racing/horse_racing/neural_networks/data.csv',1,0);
data_main = data(:, 2:12);
net = feedforwardnet([9 10 8 1]);
net.layers{1}.transferFcn = 'logsig';
net.layers{2}.transferFcn = 'radbas';
net.layers{3}.transferFcn = 'radbas';
net.layers{4}.transferFcn = 'purelin';
net.trainParam.epochs = 20;
[net,tr] = train(net,data_main(:,2:11)',data_main(:,1)');
output = net(data_main(tr.testInd,2:11)');
indices = zeros(1,size(tr.testInd,2));
test = data_main(tr.testInd, 1);
indices(find(output > 0.5)) = 1;
accuracy_50 = sum (indices == data_main(tr.testInd,1)')/size(tr.testInd,2)
indices_class1 =  find(output > 0.8);
indices_class2 =  find(output < 0.2);
accuracy_80 = (sum(test(indices_class2) == 0) + sum(test(indices_class1) == 1))/(size(indices_class1,2) + size(indices_class2,2))


