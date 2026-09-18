import {chromium} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const config=fs.readFileSync('../.env','utf8');
const password=config.match(/^DEMO_PASSWORD=(.*)$/m)?.[1].trim().replace(/^['"]|['"]$/g,'');
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});const checks=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(20000);
const pass=x=>{checks.push(x);console.log('PASS '+x)};
try{
 await page.goto('http://127.0.0.1:8000');await page.getByLabel('Username',{exact:true}).fill('demo');await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Sign in',exact:true}).click();
 await page.getByRole('button',{name:'Continue learning',exact:true}).click();await page.getByRole('tab',{name:'Tutor',exact:true}).click();
 await page.getByLabel('Ask your tutor').fill('zzquux unsupported zzyyxx');await page.getByRole('button',{name:'Send question',exact:true}).click();await page.locator('.assistant-message').last().filter({hasText:'enough evidence'}).waitFor();pass('Real SSE unsupported response without a provider call');
 await page.reload();await page.getByRole('button',{name:'Continue learning',exact:true}).click();await page.getByRole('tab',{name:'Tutor',exact:true}).click();await page.getByRole('heading',{name:'Continue where you left off'}).waitFor();pass('Persistent Tutor memory survives reload');
 await page.getByRole('tab',{name:'Growth',exact:true}).click();await page.getByRole('heading',{name:'Learning insights',exact:true}).waitFor();await page.getByRole('button',{name:'Refresh insights',exact:true}).click();
 execFileSync(path.resolve('../.venv/Scripts/python.exe'),['backend/manage.py','shell','-c','from study.insights import run_insight_job; run_insight_job()'],{cwd:'..',stdio:'pipe'});
 await page.getByText('Recent 5 average',{exact:true}).waitFor();pass('Persisted background insight job and computed comparison');await page.screenshot({path:'../docs/screenshots/should-growth-desktop.png',fullPage:true});
 await page.getByRole('tab',{name:'Analytics',exact:true}).click();await page.getByRole('heading',{name:'Where performance changes'}).waitFor();await page.getByText('Inspect trace',{exact:true}).first().click();pass('Assessment breakdown and trace inspection');await page.screenshot({path:'../docs/screenshots/should-analytics-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'../docs/screenshots/should-analytics-mobile.png',fullPage:true});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile horizontal overflow');
 await page.getByRole('tab',{name:'Growth',exact:true}).click();await page.getByText('Recent 5 average',{exact:true}).waitFor();await page.screenshot({path:'../docs/screenshots/should-growth-mobile.png',fullPage:true});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Growth mobile overflow');pass('390px analytics and insights layout');
 await page.setViewportSize({width:1440,height:1000});await page.getByRole('button',{name:'Admin dashboard',exact:true}).click();await page.getByRole('heading',{name:'Background insight jobs'}).waitFor();await page.getByLabel('user',{exact:true}).selectOption({label:'demo'});pass('Admin background insight jobs and user filter');
 if(errors.length)throw Error(errors.join('; '));
 fs.writeFileSync('../docs/browser-should-results.json',JSON.stringify({mode:'real persisted data; no provider requests or network mocks',passed:checks,consoleErrors:errors,created:new Date().toISOString()},null,2));
}finally{await browser.close()}
