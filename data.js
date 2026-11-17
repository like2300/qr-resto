// Données du restaurant (modifiez ici votre menu). Prix en FCFA.
const RESTAURANT = { name: "Mon Restaurant", currency: "FCFA", vatRate: 0 };
const TABLES = ["Table 1", "Table 2", "Table 3", "Table 4"];
const MENU = [
  { cat: "Pizzas", items: [
    { id: 1, name: "Pizza Margherita", price: 7871, desc: "Tomate, mozzarella, basilic" },
    { id: 2, name: "Pizza Pepperoni", price: 9183, desc: "Pepperoni, mozzarella" },
    { id: 3, name: "Pizza Végétarienne", price: 8527, desc: "Légumes grillés, mozzarella" },
    { id: 4, name: "Pizza Prosciutto", price: 10495, desc: "Jambon cru, roquette" }
  ]},
  { cat: "Plats", items: [
    { id: 5, name: "Poulet braisé", price: 5000, desc: "Servi avec manioc" },
    { id: 6, name: "Manioc", price: 1000, desc: "Bâton de manioc" }
  ]},
  { cat: "Boissons", items: [
    { id: 7, name: "Bavaria 0.0 30cl", price: 1500, desc: "Bière sans alcool", img: "bavaria.jpg" },
    { id: 8, name: "Jus naturel", price: 2000, desc: "Fruits frais pressés" }
  ]}
];
const fmt = n => Number(n).toLocaleString("fr-FR") + " " + RESTAURANT.currency;
const STATUS = { pending:"En attente", preparing:"En préparation", ready:"Prête", served:"Servie", cancelled:"Annulée" };
const loadOrders = () => JSON.parse(localStorage.getItem("orders") || "[]");
const saveOrders = o => localStorage.setItem("orders", JSON.stringify(o));
