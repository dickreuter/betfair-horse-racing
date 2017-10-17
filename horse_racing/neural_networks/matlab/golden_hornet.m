%% TRAINING
% Load Data
colNames = {'LTP', 'NoHorses', 'MinLastLTPs', 'MaxLastLTPs', 'MeanLastLTPs', 'MedianLastLTPs', ...
    'VarianceLastLTPs', 'SkewLastLTPs', 'KurtosisLastLTPs', 'MinLastHourLTPs', 'MaxLastHourLTPs', ...
    'MeanLastHourLTPs', 'MedianLastHourLTPs', 'VarianceLastHourLTPs', 'SkewLastHourLTPs', ...
    'KurtosisLastHourLTPs', 'Winner'};
data = array2table(csvread('c:\Users\Claudio\Git\horse_racing\horse_racing\neural_networks\golden_hornet_training_data.csv',0,0), 'VariableNames', colNames);
% data = array2table(csvread('c:\Users\Claudio\Git\horse_racing\horse_racing\neural_networks\golden_hornet_backtesting_data.csv',0,0), 'VariableNames', colNames);
[trainedModel, validationAccuracy] = trainClassifier(data);

%% Analyze LTP vs Kurtosis
% Histograms for Skew and Kurtosis
histogram(data.SkewLastLTPs)
histogram(data.KurtosisLastLTPs)
histogram(data.SkewLastHourLTPs)
histogram(data.KurtosisLastHourLTPs)

%%
index_wins = find(data.Winner == 1);
index_losses = find(data.Winner == 0);
data_wins = data(index_wins, :);
data_losses = data(index_losses, :);
% Plot
fullscreen=get(0,'ScreenSize');
f1=figure('Position',[0 0 fullscreen(3) fullscreen(4)],'Name','Historical Bets');
scatter(data_losses.LTP, data_losses.KurtosisLastHourLTPs, 'b', 'filled')
hold on
scatter(data_wins.LTP, data_wins.KurtosisLastHourLTPs, 'r', 'filled')
xlabel('LTP')
ylabel('KurtosisLastHourLTPs')
grid on

% Golden Boundary Curve
a = 30;
b = 0.9;
lower_lim = 0;
upper_lim = 100;
x_curve = linspace(lower_lim, upper_lim, 100);
y_curve = a * b .^ x_curve;
% y_curve = -1 .* x_curve + 20;
plot(x_curve, y_curve, '-g', 'linewidth', 2);
legend('Losses', 'Wins', 'Golden Curve');
% print(f1,'-dtiff','C:\temp\Historical Bets','-r300');
xlim([19, 71]);
ylim([0, 5]);
% print(f1,'-dtiff','C:\temp\Historical Bets Zoomed','-r300');

%% Identify Wins/Losses proportions falling withing the golden region
golden_losses_idx = find(data_losses.KurtosisLastHourLTPs <= a * b .^ data_losses.LTP & data_losses.LTP <= 60);
golden_wins_idx = find(data_wins.KurtosisLastHourLTPs <= a * b .^ data_wins.LTP & data_wins.LTP <= 60);
f2=figure('Position',[0 0 fullscreen(3) fullscreen(4)],'Name','Golden Area Wins/Losses Proportions');
scatter(data_losses.LTP(golden_losses_idx), data_losses.KurtosisLastHourLTPs(golden_losses_idx), 'b', 'filled');
hold on
scatter(data_wins.LTP(golden_wins_idx), data_wins.KurtosisLastHourLTPs(golden_wins_idx), 'r', 'filled');
plot(linspace(1, 60, 100), a * b .^ linspace(0, 60, 100), '-g', 'linewidth', 2);
title(['Wins = ', num2str(size(golden_wins_idx, 1)), '   ', 'Losses = ', num2str(size(golden_losses_idx, 1)), '   ', 'Ratio = ', num2str(size(golden_losses_idx, 1) / size(golden_wins_idx, 1))]);
xlabel('LTP')
ylabel('KurtosisLastHourLTPs')
grid on
legend('Losses', 'Wins', 'Golden Curve')
text(30, 30, ['y = ', num2str(a), ' * ', num2str(b), ' ^ x'], 'HorizontalAlignment', 'right', 'FontSize', 18);
% print(f2,'-dtiff','C:\temp\Golden Area','-r300');

%% Neural Network
net = feedforwardnet([16 64 128 64 32]);
net.layers{1}.transferFcn = 'logsig';
net.layers{2}.transferFcn = 'tansig';
net.layers{3}.transferFcn = 'tansig';
net.layers{4}.transferFcn = 'tansig';
net.layers{5}.transferFcn = 'logsig';
net.trainParam.epochs = 200;
view(net);
[net, tr] = train(net, data(:, 1:16)', data(:, 17)', 'useGPU', 'yes', 'showResources', 'yes');
plotperform(tr)

% Filtered Performances on Test Dataset
output = net(data(tr.testInd, 1:16)');
indices = zeros(1, size(tr.testInd,2));
test = data(tr.testInd, 17);

% Back-only with confidence > 50%
indices(find(output > 0.5)) = 1;
accuracy_50 = sum (indices == data(tr.testInd, 17)') / size(tr.testInd, 2)

% Back-Lay strategy with confidence < 30% for Lay and > 70% for Back
indices_back =  find(output > 0.7);
indices_lay =  find(output < 0.3);
accuracy_80 = (sum(test(indices_lay) == 0) + sum(test(indices_back) == 1))/(size(indices_back,2) + size(indices_lay,2))
output_back = NaN(size(output));
output_lay = NaN(size(output));
output_back(indices_back) = output(indices_back);
output_lay(indices_lay) = output(indices_lay);
output(indices_back) = NaN;
output(indices_lay) = NaN;
x_marks = 1:1:size(output, 2);
scatter(x_marks, output, 'b', 'filled');
hold on
scatter(x_marks, output_back, 'r', 'filled');
scatter(x_marks, output_lay, 'g', 'filled');

% Regression Plots
Outputs = net(data(:, 1:16)');
trOut = Outputs(tr.trainInd);
vOut = Outputs(tr.valInd);
tsOut = Outputs(tr.testInd);
trTarg = data(tr.trainInd, 17);
vTarg = data(tr.valInd, 17);
tsTarg = data(tr.testInd, 17);
plotregression(trTarg, trOut, 'Train', vTarg, vOut, 'Validation', tsTarg, tsOut, 'Testing')

%% BACKTESTING / VALIDATION
% Load Backtesting data for 2017
data_bt = array2table(csvread('c:\Users\Claudio\Git\horse_racing\horse_racing\neural_networks\backtesting_data_golden_hornet.csv',1,0), 'VariableNames', colNames);

% Predictions Analysis
predictions = trainedModel.predictFcn(data_bt(:, 1:16));
exact = data_bt{:, 17};
ltp = data_bt{:, 1};