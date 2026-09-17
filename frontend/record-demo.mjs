import {chromium} from '@playwright/test';
import fs from 'node:fs';
const browser=await chromium.launch({channel:'chrome',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000},recordVideo:{dir:'test-results/final-video',size:{width:1440,height:1000}}});const page=await context.newPage();const start=Date.now();const chapters=[];const scene=async(text,ms=5000)=>{chapters.push({time:(Date.now()-start)/1000,text});console.log(text);await page.waitForTimeout(ms)};
try{
 await page.goto('http://127.0.0.1:8000');await page.getByLabel('Username',{exact:true}).fill('demo');await page.getByLabel('Password',{exact:true}).fill(process.env.DEMO_PASSWORD);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('heading',{name:'A good day to learn something.'}).waitFor();
 await scene('Real persisted Gemini results - labeled demo material, no fabricated scores');
 await page.getByRole('button',{name:'Continue learning',exact:true}).click();await page.getByRole('tab',{name:'Materials',exact:true}).click();await page.getByText('ready',{exact:true}).waitFor();await scene('Persistent PDF processing - page-aware material is ready');
 await page.getByRole('tab',{name:'Tutor',exact:true}).click();await page.locator('.citations a').first().waitFor();await scene('Grounded Tutor answer with a verifiable document and page citation',6000);
 const tabPromise=context.waitForEvent('page');await page.locator('.citations a').first().click();const sourceTab=await tabPromise;await sourceTab.waitForLoadState('domcontentloaded');await page.waitForTimeout(1500);await sourceTab.close();
 await page.locator('.chat-messages').evaluate(e=>e.scrollTop=e.scrollHeight);await scene('Unsupported questions explicitly state insufficient evidence');
 await page.getByRole('tab',{name:'Quiz',exact:true}).click();await page.locator('.history-item').filter({hasText:'100%'}).first().click();await page.locator('.feedback').waitFor();await scene('Adaptive MCQ - explanatory feedback and a persisted mastery update',6000);
 const open=page.locator('.history-item').filter({hasText:'Open-ended'}).first();if(await open.count()){await open.click();await page.getByLabel('Your explanation',{exact:true}).fill('The Calvin cycle occurs in the stroma. ATP and NADPH power carbon fixation to form G3P.');}
 await scene('Open question is real; further live grading is blocked by Gemini quota',7000);
 await page.getByRole('tab',{name:'Growth',exact:true}).click();await page.getByRole('heading',{name:'Mastery evidence over time'}).waitFor();await scene('Concept mastery, evidence history and actionable next steps',6000);
 await page.getByRole('tab',{name:'Analytics',exact:true}).click();await page.getByRole('heading',{name:'AI usage & reliability'}).waitFor();await scene('Project analytics derive from actual persisted learning events');
 await page.getByRole('button',{name:'Global analytics',exact:true}).click();await scene('Global analytics aggregate learning activity across projects',4000);
 await page.getByRole('button',{name:'Home',exact:true}).click();await page.setViewportSize({width:390,height:844});await scene('Responsive mobile layout and working sidebar navigation',5000);await page.setViewportSize({width:1440,height:1000});
 await page.getByRole('button',{name:'Admin dashboard',exact:true}).click();await page.getByRole('heading',{name:'Background jobs & failures'}).waitFor();await page.getByLabel('user',{exact:true}).selectOption({label:'demo'});await scene('Admin drill-down - learner activity, assessments, progress and AI usage',5000);
 await page.getByRole('heading',{name:'Background jobs & failures'}).scrollIntoViewIfNeeded();await scene('Jobs, failures and live evaluation results remain inspectable',6000);
 const path=await page.video().path();fs.writeFileSync('../docs/demo-recording-metadata.json',JSON.stringify({mainVideo:path,chapters,duration:(Date.now()-start)/1000,mode:'Real recorded UI. No new provider calls. Open grading blocked by quota.'},null,2));
}finally{await context.close();await browser.close()}
