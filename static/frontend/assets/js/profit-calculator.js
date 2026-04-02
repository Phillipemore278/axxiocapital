let accountSize = 10000;
    let profitRate = 0.005;
    let monthlyProfit = 0;

    function setAccountSize(size) {
      accountSize = size;
      document.getElementById('accountSizeLabel').innerHTML = '$' + accountSize.toLocaleString();
    }

    function setProfitRate(rate) {
      profitRate = rate;
      document.getElementById('profitRateLabel').innerHTML = (profitRate * 100) + '%';
    }

    function updateAccountSize(value) {
      setAccountSize(parseInt(value));
    }

    function updateProfitRate(value) {
      setProfitRate(parseFloat(value));
    }

    function setMonthlyProfit(profit) {
      monthlyProfit = profit;
    }

    function startTrading() {
      const totalProfit = accountSize * profitRate;
      const totalMonthlyProfit = totalProfit + monthlyProfit;
      document.getElementById('result').innerHTML = 'Total Monthly Profit: $' + totalMonthlyProfit.toFixed(2);
    }