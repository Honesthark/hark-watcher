// Nox-style on-chain alerts for AIN, Q, BTW (BSC) and IRYS (Ethereum). Prints one JSON line per notable transfer.
import {ethers} from "ethers";
import fs from "fs";
const D="scripts/"; const S="state/onchain.json";
const L=JSON.parse(fs.readFileSync(D+"labels.json")); const st=fs.existsSync(S)?JSON.parse(fs.readFileSync(S)):{};
const T=[
 {sym:"AIN",chain:"bsc",addr:"0x9558a9254890B2A8B057a789F413631B9084f4a3",mexc:"AIN_USDT"},
 {sym:"Q",chain:"bsc",addr:"0xc07e1300dc138601FA6B0b59f8D0FA477e690589",mexc:"Q_USDT"},
 {sym:"BTW",chain:"bsc",addr:"0x444045B0EE1ee319A660a5E3d604CA0ffA35ACaA",mexc:"BTW_USDT"},
 {sym:"IRYS",chain:"ethereum",addr:"0x50f41F589aFACa2EF41FDF590FE7b90cD26DEe64",mexc:"IRYS_USDT"}];
const RPC={bsc:["https://bsc-rpc.publicnode.com","https://bsc-mainnet.public.blastapi.io"],ethereum:["https://ethereum-rpc.publicnode.com"]};
const MAXB={bsc:6000,ethereum:600}, CH={bsc:1000,ethereum:200};
const MIN_USD=Number(process.env.MIN_USD||150000), MIN_MCAP=Number(process.env.MIN_MCAP||0.01);
const TOPIC=ethers.id("Transfer(address,address,uint256)");
const j=async u=>(await fetch(u,{headers:{"user-agent":"curl/8.5.0"}})).json();
const lab=a=>L[a.toLowerCase()]||null;
for (const t of T){
 try{
  let p; for(const r of RPC[t.chain]){ try{p=new ethers.JsonRpcProvider(r,undefined,{staticNetwork:true}); await p.getBlockNumber(); break;}catch{p=null} }
  if(!p){console.log(JSON.stringify({sym:t.sym,error:"rpc"}));continue}
  const c=new ethers.Contract(t.addr,["function decimals() view returns(uint8)"],p);
  const dec=Number(await c.decimals()); const head=await p.getBlockNumber();
  let from=st[t.sym]?st[t.sym]+1:head-MAXB[t.chain]; if(head-from>MAXB[t.chain]) from=head-MAXB[t.chain];
  const ds=await j(`https://api.dexscreener.com/latest/dex/tokens/${t.addr}`); const pr=(ds.pairs||[]).filter(x=>x.chainId===t.chain).sort((a,b)=>(b.liquidity?.usd||0)-(a.liquidity?.usd||0))[0]||{};
  const mx=(await j(`https://contract.mexc.com/api/v1/contract/ticker?symbol=${t.mexc}`)).data||{};
  const det=(await j(`https://contract.mexc.com/api/v1/contract/detail?symbol=${t.mexc}`)).data||{};
  const price=Number(mx.lastPrice||pr.priceUsd||0), mcap=Number(pr.marketCap||pr.fdv||0);
  const oi=Number(mx.holdVol||0)*Number(det.contractSize||1)*price;
  const mkt={price,mcap,vol24_mexc_usd:Number(mx.amount24||0),dex_vol24:pr.volume?.h24||0,chg24:Number(mx.riseFallRate||0)*100,oi_usd_mexc:oi,funding:Number(mx.fundingRate||0)};
  let logs=[]; for(let b=from;b<=head;b+=CH[t.chain]){ const e=Math.min(b+CH[t.chain]-1,head); try{logs.push(...await p.getLogs({address:t.addr,topics:[TOPIC],fromBlock:b,toBlock:e}))}catch(err){console.log(JSON.stringify({sym:t.sym,warn:"getLogs "+b+"-"+e}))} }
  st[t.sym]=head;
  for(const l of logs){
   if(l.topics.length<3) continue;
   const fr="0x"+l.topics[1].slice(26), to="0x"+l.topics[2].slice(26);
   const amt=Number(ethers.formatUnits(l.data,dec)), usd=amt*price;
   const lf=lab(fr), lt=lab(to);
   const big = usd>=MIN_USD || (mcap && usd/mcap>=MIN_MCAP);
   if(!big) continue;
   const ex=s=>s?s.split(":")[0]:null;
   let kind="WHALE TRANSFER";
   if(lf&&lt&&ex(lf)===ex(lt)) kind=lf.includes("Cold")&&lt.includes("Hot")?"COLD TO HOT":lf.includes("Hot")&&lt.includes("Cold")?"HOT TO COLD":"INTERNAL EXCHANGE";
   else if(lt&&!lf&&ex(lt)!=="Burn"&&!lt.startsWith("Mint")) kind="EXCHANGE DEPOSIT";
   else if(lf&&!lt&&!lf.startsWith("Mint")) kind="EXCHANGE WITHDRAWAL";
   else if(lf&&lt) kind="EXCHANGE TO EXCHANGE";
   if(lf?.startsWith("Mint")) kind="MINT"; if(lt==="Burn"||lt?.startsWith("Mint")) kind="BURN";
   console.log(JSON.stringify({sym:t.sym,chain:t.chain,kind,amount:Math.round(amt),usd:Math.round(usd),pct_mcap:mcap?+(usd/mcap*100).toFixed(2):null,pct_vol:mkt.vol24_mexc_usd?+(usd/mkt.vol24_mexc_usd*100).toFixed(2):null,from:fr,from_label:lf,to,to_label:lt,tx:l.transactionHash,...mkt}));
  }
  console.log(JSON.stringify({sym:t.sym,info:`scanned ${from}-${head}`,logs:logs.length,...mkt}));
 }catch(e){console.log(JSON.stringify({sym:t.sym,error:String(e.shortMessage||e.message).slice(0,150)}))}
}
fs.writeFileSync(S,JSON.stringify(st));
