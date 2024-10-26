import React, { useState, useEffect } from 'react';
import { PlusCircle, Trash2, DollarSign, Settings, PieChart, Home } from 'lucide-react';

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Expense {
  id: number;
  date: string;
  name: string;
  price: number;
}

export default function ExpenseTracker() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [itemName, setItemName] = useState('');
  const [itemPrice, setItemPrice] = useState('');
  const [currency, setCurrency] = useState('RON');
  const [salary, setSalary] = useState('');
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>({});

  useEffect(() => {
    fetchExchangeRates();
  }, []);

  const fetchExchangeRates = async () => {
    try {
      const response = await fetch("https://api.exchangerate-api.com/v4/latest/RON");
      const data = await response.json();
      setExchangeRates(data.rates);
    } catch (error) {
      console.error("Error fetching exchange rates:", error);
    }
  };

  const addExpense = () => {
    if (itemName && itemPrice) {
      const newExpense: Expense = {
        id: Date.now(),
        date: new Date().toLocaleDateString(),
        name: itemName,
        price: parseFloat(itemPrice),
      };
      setExpenses([...expenses, newExpense]);
      setItemName('');
      setItemPrice('');
    }
  };

  const removeExpense = (id: number) => {
    setExpenses(expenses.filter(expense => expense.id !== id));
  };

  const formatPrice = (amount: number, curr: string) => {
    const rate = exchangeRates[curr] || 1;
    return `${curr} ${(amount * rate).toFixed(2)}`;
  };

  const totalExpense = expenses.reduce((sum, expense) => sum + expense.price, 0);
  const remainingSalary = parseFloat(salary) - totalExpense;

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="bg-white dark:bg-gray-800 shadow-md">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-orange-500">ExpenseTracker</h1>
          <nav className="hidden md:flex space-x-4">
            <Button variant="ghost"><Home className="mr-2 h-4 w-4" /> Home</Button>
            <Button variant="ghost"><PieChart className="mr-2 h-4 w-4" /> Reports</Button>
            <Button variant="ghost"><Settings className="mr-2 h-4 w-4" /> Settings</Button>
          </nav>
          <Select value={currency} onValueChange={setCurrency}>
            <SelectTrigger className="w-[100px]">
              <SelectValue placeholder="Currency" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="RON">RON</SelectItem>
              <SelectItem value="USD">USD</SelectItem>
              <SelectItem value="EUR">EUR</SelectItem>
              <SelectItem value="LKR">LKR</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Add Expense</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Input
                  type="text"
                  placeholder="Item Name"
                  value={itemName}
                  onChange={(e) => setItemName(e.target.value)}
                />
                <Input
                  type="number"
                  placeholder={`Item Price (${currency})`}
                  value={itemPrice}
                  onChange={(e) => setItemPrice(e.target.value)}
                />
                <Button onClick={addExpense} className="w-full">
                  <PlusCircle className="mr-2 h-4 w-4" /> Add Expense
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Monthly Salary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Input
                  type="number"
                  placeholder="Monthly Salary (RON)"
                  value={salary}
                  onChange={(e) => setSalary(e.target.value)}
                />
                <div className="text-lg font-semibold">
                  Remaining Salary: {formatPrice(remainingSalary, currency)}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Expense List</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Item Name</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {expenses.map((expense) => (
                  <TableRow key={expense.id}>
                    <TableCell>{expense.date}</TableCell>
                    <TableCell>{expense.name}</TableCell>
                    <TableCell>{formatPrice(expense.price, currency)}</TableCell>
                    <TableCell>
                      <Button variant="destructive" size="sm" onClick={() => removeExpense(expense.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="mt-4 text-xl font-bold">
              Total Expense: {formatPrice(totalExpense, currency)}
            </div>
          </CardContent>
        </Card>
      </main>

      <footer className="bg-white dark:bg-gray-800 shadow-md mt-8">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-gray-600 dark:text-gray-400">
          &copy; 2024 ExpenseTracker. All rights reserved.
        </div>
      </footer>
    </div>
  );
}